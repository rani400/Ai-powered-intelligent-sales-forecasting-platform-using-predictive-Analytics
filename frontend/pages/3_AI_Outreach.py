"""Module 3: Reviewable email drafts, enriched by Module 4 strategy."""
import streamlit as st
from frontend.components.api import call, lead_picker, ApiError
from frontend.components.style import hero

hero('AI Outreach', 'Write informed messages with human review, no automatic sending.')
st.info('This application generates drafts only and does not automatically send emails.')
lead = lead_picker('outreach_lead')

st.subheader('Outreach strategy')
try:
    score = call('GET', f"/api/scoring/{lead['lead_id']}")
except ApiError:
    score = None
if score:
    m1, m2, m3 = st.columns(3)
    m1.metric('Lead score', f"{score['score']:g}/100")
    m2.metric('Conversion estimate', f"{100*score['conversion_probability']:.1f}%")
    m3.metric('Recommended action', score['recommended_action'])
    st.caption(f"{score['recommendation_reason']} · Mode: {score['prediction_mode']} (synthetic demo ML or heuristic)")
else:
    st.warning('No saved strategy for this prospect. Generate a score on the Lead Scoring page for better context.')
    if st.button('Compute strategy for this lead'):
        try:
            call('POST', f"/api/scoring/{lead['lead_id']}/score")
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))

st.subheader('Compose a personalized draft')
with st.form('outreach_generator'):
    c1, c2, c3 = st.columns(3)
    tone = c1.selectbox('Tone', ['Professional', 'Friendly', 'Concise', 'Persuasive'])
    goals = ['Introduction', 'Discovery call', 'Follow-up', 'Meeting request', 'Re-engagement']
    suggested = score['suggested_outreach_goal'] if score else 'Introduction'
    goal = c2.selectbox('Communication goal', goals, index=goals.index(suggested) if suggested in goals else 0)
    length = c3.selectbox('Email length', ['Short', 'Medium', 'Long'], index=1)
    submit = st.form_submit_button('Generate email draft', type='primary')
if submit:
    with st.spinner('Preparing your draft…'):
        try:
            result = call('POST', '/api/outreach/generate', json={
                'lead_id': lead['lead_id'], 'tone': tone, 'communication_goal': goal, 'email_length': length})
            st.session_state[f"draft_{lead['lead_id']}"] = result
        except ApiError as exc:
            st.error(str(exc))
result = st.session_state.get(f"draft_{lead['lead_id']}")
if result:
    st.divider()
    st.markdown('### Generated draft')
    
    st.caption(f"Requested: {result['email_length']} · Actual body: {len(result['email_content'].split())} words")
    st.text_input('Subject (copy or edit)', result['email_subject'], key=f"subject_{result['campaign_id']}")
    st.text_area('Email body (copy or edit)', result['email_content'], height=260, key=f"body_{result['campaign_id']}")
    st.caption('Edits here are for copying only; the saved generated draft is unchanged. No email is sent.')

st.divider()
st.subheader('Saved draft history')
try:
    history = call('GET', f"/api/outreach/leads/{lead['lead_id']}/drafts")
    if history:
        for item in history:
            with st.expander(f"{item['created_at'][:16].replace('T', ' ')} · {item['email_subject']}"):
                st.caption(f"{item['tone']} | {item['communication_goal']} | {'Local template' if item['is_mock'] else item['provider']} | DRAFT")
                st.code(item['email_content'], language=None)
    else:
        st.caption('No drafts yet. Generate one above to begin.')
except ApiError as exc:
    st.error(str(exc))
