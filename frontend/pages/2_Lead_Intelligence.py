"""Module 2: Evidence-bounded company context and qualification."""
import streamlit as st
from frontend.components.api import call, lead_picker, show_factors, ApiError
from frontend.components.style import hero

hero('Lead Intelligence', 'Understand a prospect using available information—without inventing company facts.')
lead = lead_picker('intelligence_lead')
left, right = st.columns([2, 1])
with left:
    st.write(f"**Prospect:** {lead['company_name']}  ·  {lead.get('industry') or 'Industry not recorded'}")
with right:
    run = st.button('Analyze lead', type='primary', use_container_width=True)

try:
    if run:
        with st.spinner('Preparing structured insights…'):
            result = call('POST', f"/api/intelligence/{lead['lead_id']}/analyze")
        st.success('Analysis saved for review.')
    else:
        try:
            result = call('GET', f"/api/intelligence/{lead['lead_id']}")
        except ApiError as exc:
            if '404' in str(exc):
                st.info('No analysis yet. Select **Analyze lead** to generate one.')
                st.stop()
            raise
except ApiError as exc:
    st.error(str(exc))
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric('Qualification score', f"{result['qualification_score']:g} / 100")
c2.metric('Qualification band', result['qualification_band'])
c3.metric('Missing information', len(result['information_gaps']))
st.caption('Qualification is a transparent rules-based assessment, not a trained ML prediction.')
st.subheader('Company snapshot')
st.write(result['company_summary'])
st.markdown('**Industry context (general, not verified for this company)**')
st.write(result['industry_context'])

c1, c2 = st.columns(2, gap='large')
with c1:
    st.markdown('### Potential needs')
    for item in result['potential_needs']:
        st.write('•', item)
    st.markdown('### Potential opportunities')
    for item in result['potential_opportunities']:
        st.write('•', item)
with c2:
    st.markdown('### Observations')
    for item in result['observations']:
        st.write('•', item)
    st.markdown('### Information gaps')
    for item in result['information_gaps']:
        st.write('•', item)

with st.expander('How the qualification score was calculated', expanded=False):
    st.caption(result['methodology'])
    show_factors(result['contributing_factors'])
