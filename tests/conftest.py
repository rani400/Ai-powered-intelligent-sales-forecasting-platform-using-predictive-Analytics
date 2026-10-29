import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import Base, get_db, make_engine
from app import models  # noqa


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f'sqlite:///{tmp_path / "test.db"}')
    Base.metadata.create_all(engine)

    def override_db():
        with Session(bind=engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def sample():
    return {'company_name': 'Sample Tech', 'industry': 'Technology', 'contact_name': 'Sam Test',
            'email': 'sam@example.org', 'phone': '555-123-4567', 'lead_status': 'New',
            'company_size': '11-50', 'engagement_score': 50}


@pytest.fixture
def created(client, sample):
    response = client.post('/api/leads', json=sample)
    assert response.status_code == 201, response.text
    return response.json()
