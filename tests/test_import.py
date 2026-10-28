import io


def upload(client, content, policy='reject', filename='leads.csv'):
    return client.post('/api/leads/import', params={'duplicate_policy': policy},
                       files={'file': (filename, content.encode('utf-8'), 'text/csv')})


def test_import_multirow_partial(client):
    text = ('company_name,email,engagement_score,lead_status\n'
            'Alpha,alpha@example.org,52,New\n'
            'Bad Mail,broken-mail,45,New\n'
            'Beta,beta@example.org,78,Qualified\n'
            'Wrong Stage,wrong@example.org,20,Unknown\n')
    r = upload(client, text)
    assert r.status_code == 200, r.text
    assert r.json()['inserted'] == 2
    assert r.json()['rejected'] == 2
    assert [x['row'] for x in r.json()['issues']] == [3, 5]
    assert client.get('/api/leads').json()['total'] == 2


def test_import_duplicate_reject(client):
    text = 'company_name,email\nAlpha,alpha@example.org\nAlpha,alpha@example.org\n'
    result = upload(client, text).json()
    assert result['inserted'] == 1
    assert result['duplicate'] == result['rejected'] == 1
    assert result['issues'][0]['reason_code'] == 'DUPLICATE_LEAD'


def test_import_duplicate_skip(client):
    result = upload(client, 'company_name,email\nAlpha,a@example.org\nAlpha,a@example.org\n', 'skip').json()
    assert result['inserted'] == 1
    assert result['skipped'] == 1
    assert result['duplicate'] == 1
    assert result['rejected'] == 0


def test_import_duplicate_update(client):
    text = 'company_name,email,engagement_score\nAlpha,a@example.org,10\nAlpha,a@example.org,77\n'
    result = upload(client, text, 'update_existing').json()
    assert result['inserted'] == 1
    assert result['updated'] == 1
    assert result['duplicate'] == 1
    assert client.get('/api/leads').json()['items'][0]['engagement_score'] == 77


def test_import_missing_company(client):
    r = upload(client, 'company_name,email\n,unknown@example.org\n')
    assert r.json()['rejected'] == 1
    assert r.json()['inserted'] == 0


def test_import_bad_number(client):
    r = upload(client, 'company_name,email,engagement_score\nAcme,a@example.org,very_high\n')
    assert r.json()['rejected'] == 1


def test_import_bad_header(client):
    r = upload(client, 'name,email\nAcme,a@example.org\n')
    assert r.status_code == 400


def test_import_wrong_extension(client):
    r = upload(client, 'company_name\nAcme', filename='data.txt')
    assert r.status_code == 400


def test_import_bad_policy(client):
    r = upload(client, 'company_name\nAcme', policy='overwrite_all')
    assert r.status_code == 422


def test_import_row_normalization(client):
    r = upload(client, 'company name,email,lead status\n  Alpha  ,TEST@EXAMPLE.ORG,qualified\n')
    assert r.json()['inserted'] == 1
    saved = client.get('/api/leads').json()['items'][0]
    assert saved['email'] == 'test@example.org'
    assert saved['lead_status'] == 'Qualified'
