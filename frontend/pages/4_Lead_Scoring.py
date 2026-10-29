"""Module 4: Explainable lead priority, synthetic-demo conversion prediction, next action."""
import streamlit as st
from frontend.components.api import call, lead_picker, show_factors, ApiError
from frontend.components.style import hero

hero('Lead Scoring & Recommendations', 'Prioritize pipeline outreach using transparent signals and a demonstrative conversion model.')
lead = lead_picker('scoring_lead')
col, btn = st.columns([3, 1])
with col:
    st.write(f"**Selected prospect:** {lead['company_name']}  ·  {lead['lead_status']}")
with btn:
    compute = st.button('Calculate score', type='primary', use_container_width=True)
try:
    if compute:
        with st.spinner('Calculating score and estimate…'):
            result = call('POST', f"/api/scoring/{lead['lead_id']}/score")
        st.success('Score and recommendation saved.')
    else:
        try:
            result = call('GET', f"/api/scoring/{lead['lead_id']}")
        except ApiError as exc:
            if '404' in str(exc):
                st.info('No score available. Select **Calculate score** to begin.')
                st.stop()
            raise
except ApiError as exc:
    st.error(str(exc))
    st.stop()

m1, m2, m3 = st.columns(3)
m1.metric('Explainable priority', f"{result['score']:g} / 100")
m2.metric('Priority band', result['priority_band'])
m3.metric('Estimated conversion', f"{100*result['conversion_probability']:.1f}%")
if result['prediction_mode'] == 'observed_converted':
    st.info('The lead is already marked Converted. 100% reflects the recorded stage, not a forecast.')
elif result['prediction_mode'] == 'demo_ml':
    st.warning('Demonstration ML model trained on SYNTHETIC data. Probability is an estimate, not a guarantee or validated real-world result.')
else:
    st.warning('Heuristic mode: model artifact unavailable. This is NOT a machine-learning prediction.')

st.subheader('Recommended next action')
st.markdown(f"### {result['recommended_action']}")
st.write(result['recommendation_reason'])
c1, c2 = st.columns(2)
c1.write(f"**Action priority:** {result['recommendation_priority']}")
c2.write(f"**Suggested outreach goal:** {result['suggested_outreach_goal']}")
for factor in result['supporting_factors']:
    st.caption('• ' + factor)

with st.expander('Score breakdown · rules-based', expanded=True):
    show_factors(result['factors'])

with st.expander('Predictive model evaluation & limitations'):
    try:
        model = call('GET', '/api/scoring/model/status')
        st.write(model['notice'])
        if model['metrics']:
            metrics = model['metrics']
            cols = st.columns(5)
            for col, field in zip(cols, ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']):
                col.metric(field.upper(), f"{100*metrics[field]:.1f}%")
            st.caption(f"Train: {metrics['train_rows']} synthetic rows; test: {metrics['test_rows']} held-out rows; random seed: {metrics['random_seed']}")
            st.caption(metrics['limitations'])
    except ApiError as exc:
        st.error(str(exc))
