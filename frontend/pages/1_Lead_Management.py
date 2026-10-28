"""Module 1: Prospect management and resilient CSV import."""
import pandas as pd
import streamlit as st
from frontend.components.api import call, ApiError
from frontend.components.style import hero

hero('Lead Management', 'Create, organize, and qualify the prospect records that power SalesGenie AI.')
try:
    response = call('GET', '/api/leads', params={'page_size': 100})
except ApiError as exc:
    st.error(str(exc))
    st.stop()
leads = response['items']

k1, k2, k3 = st.columns(3)
k1.metric('Total prospects', response['total'])
k2.metric('Active leads', sum(l['is_active'] for l in leads))
k3.metric('Qualified / Converted', sum(l['lead_status'] in ('Qualified', 'Converted') for l in leads))

tab_list, tab_new, tab_import = st.tabs(['Prospect directory', 'Add lead', 'CSV import'])
with tab_list:
    st.subheader('Your lead directory')
    c1, c2, c3 = st.columns([2, 1, 1])
    query = c1.text_input('Search by company, contact, or email', placeholder='Search prospects…')
    status_filter = c2.selectbox('Lifecycle stage', ['All', 'New', 'Contacted', 'Qualified', 'Converted'])
    industries = sorted({l['industry'] for l in leads if l['industry']})
    industry_filter = c3.selectbox('Industry', ['All'] + industries)
    params = {'search': query or None, 'lead_status': None if status_filter == 'All' else status_filter,
              'industry': None if industry_filter == 'All' else industry_filter, 'page_size': 100}
    try:
        filtered = call('GET', '/api/leads', params={k: v for k, v in params.items() if v is not None})['items']
    except ApiError as exc:
        st.error(str(exc))
        st.stop()
    if filtered:
        frame = pd.DataFrame(filtered)[['lead_id', 'company_name', 'contact_name', 'industry', 'email', 'lead_status', 'engagement_score']]
        frame.columns = ['ID', 'Company', 'Contact', 'Industry', 'Email', 'Stage', 'Engagement']
        st.dataframe(frame, use_container_width=True, hide_index=True)
        chosen_id = st.selectbox('View or edit a lead', [l['lead_id'] for l in filtered],
                                 format_func=lambda x: next(f"{l['company_name']} · #{x}" for l in filtered if l['lead_id'] == x),
                                 key='directory_pick')
        lead = next(l for l in filtered if l['lead_id'] == chosen_id)
        with st.expander('Lead details and editing', expanded=True):
            info, edit = st.columns([1, 2], gap='large')
            with info:
                st.markdown(f"### {lead['company_name']}")
                st.caption(f"Created: {lead['created_at'][:10]}")
                st.write(f"**Contact:** {lead['contact_name'] or 'Not supplied'}")
                st.write(f"**Email:** {lead['email'] or 'Not supplied'}")
                st.write(f"**Phone:** {lead['phone'] or 'Not supplied'}")
                st.write(f"**Source:** {lead['source'] or 'Not supplied'}")
                st.write(f"**Size:** {lead['company_size'] or 'Not supplied'}")
                st.write(f"**Notes:** {lead['notes'] or 'None'}")
                if st.button('Delete this lead', type='secondary', key=f'delete_{chosen_id}'):
                    st.session_state.confirm_delete_id = chosen_id
                if st.session_state.get('confirm_delete_id') == chosen_id:
                    st.warning('This also removes saved analysis, scores, and drafts.')
                    if st.button('Confirm permanent deletion', type='primary'):
                        try:
                            call('DELETE', f'/api/leads/{chosen_id}')
                            st.session_state.pop('confirm_delete_id', None)
                            st.success('Lead deleted.')
                            st.rerun()
                        except ApiError as exc:
                            st.error(str(exc))
            with edit:
                with st.form(f'edit_{chosen_id}'):
                    a, b = st.columns(2)
                    company = a.text_input('Company name *', lead['company_name'])
                    contact = b.text_input('Contact person', lead['contact_name'] or '')
                    industry = a.text_input('Industry', lead['industry'] or '')
                    email = b.text_input('Email address', lead['email'] or '')
                    phone = a.text_input('Phone', lead['phone'] or '')
                    size = b.text_input('Company size', lead['company_size'] or '')
                    stage = a.selectbox('Lead status', ['New', 'Contacted', 'Qualified', 'Converted'],
                                        index=['New', 'Contacted', 'Qualified', 'Converted'].index(lead['lead_status']))
                    engagement = b.slider('Engagement score', 0, 100, int(lead['engagement_score']), key=f'eng_{chosen_id}')
                    notes = st.text_area('Notes', lead['notes'] or '', height=90)
                    active = st.checkbox('Active lead', value=lead['is_active'])
                    submitted = st.form_submit_button('Save changes', type='primary')
                if submitted:
                    payload = {'company_name': company, 'contact_name': contact or None, 'industry': industry or None,
                               'email': email or None, 'phone': phone or None, 'company_size': size or None,
                               'lead_status': stage, 'engagement_score': engagement, 'notes': notes or None, 'is_active': active}
                    try:
                        call('PATCH', f'/api/leads/{chosen_id}', json=payload)
                        st.success('Lead updated.')
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
    else:
        st.info('No prospects match these filters. Try clearing the filters or add a lead.')

with tab_new:
    st.subheader('Create a new prospect')
    with st.form('create_lead', clear_on_submit=True):
        c1, c2 = st.columns(2)
        company = c1.text_input('Company name *', placeholder='Example: Northstar Retail')
        contact = c2.text_input('Contact name')
        industry = c1.text_input('Industry')
        email = c2.text_input('Email address')
        phone = c1.text_input('Phone')
        size = c2.text_input('Company size', placeholder='e.g. 11-50')
        stage = c1.selectbox('Lifecycle stage', ['New', 'Contacted', 'Qualified', 'Converted'])
        source = c2.text_input('Lead source', placeholder='e.g. Webinar')
        engagement = st.slider('Engagement score (0–100)', 0, 100, 20)
        notes = st.text_area('Notes', height=85)
        submitted = st.form_submit_button('Add prospect', type='primary')
    if submitted:
        try:
            call('POST', '/api/leads', json={'company_name': company, 'contact_name': contact or None,
                'industry': industry or None, 'email': email or None, 'phone': phone or None,
                'company_size': size or None, 'lead_status': stage, 'engagement_score': engagement,
                'notes': notes or None, 'source': source or None})
            st.success('Prospect created successfully.')
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))

with tab_import:
    st.subheader('Import prospects from CSV')
    st.caption('Rows are checked individually. One invalid row will not prevent valid rows from importing.')
    st.code('company_name,industry,contact_name,email,phone,lead_status,company_size,engagement_score,source', language='text')
    uploaded = st.file_uploader('Choose a UTF-8 CSV file', type=['csv'])
    policy = st.radio('When a duplicate is found', ['reject', 'skip', 'update_existing'], horizontal=True,
                      help='A duplicate matches by email or company + contact name.')
    if st.button('Import CSV', disabled=uploaded is None, type='primary'):
        with st.spinner('Validating and importing records…'):
            try:
                report = call('POST', '/api/leads/import', params={'duplicate_policy': policy},
                              files={'file': (uploaded.name, uploaded.getvalue(), 'text/csv')})
                columns = st.columns(5)
                for c, field in zip(columns, ['inserted', 'rejected', 'duplicate', 'updated', 'skipped']):
                    c.metric(field.replace('_', ' ').title(), report[field])
                if report['issues']:
                    st.dataframe(pd.DataFrame(report['issues']), hide_index=True, use_container_width=True)
                else:
                    st.success('Import complete; no rejected rows.')
            except ApiError as exc:
                st.error(str(exc))
