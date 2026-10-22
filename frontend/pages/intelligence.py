"""Intelligence page - company profile, qualification score, opportunities and gaps."""

from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

from api_client import ApiError, SalesGenieApi  # noqa: E402

st.set_page_config(
    page_title="Intelligence - SalesGenie AI", page_icon="SG", layout="wide"
)

api = SalesGenieApi(st.session_state.get("api_base_url"))

st.title("Lead Intelligence")
st.write(
    "Company analysis and a transparent qualification score derived from the stored record. "
    "The score is a rule-based prioritisation heuristic, not a conversion-probability model."
)

if not api.is_reachable():
    st.error(
        "The backend is not reachable. Start it with "
        "`python -m uvicorn app.main:app --app-dir backend`."
    )
    st.stop()

try:
    listing = api.list_leads(limit=200)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load leads: {exc}")
    st.stop()

items = listing.get("items", [])
if not items:
    st.info("No leads recorded yet. Import a CSV on the Leads page first.")
    st.stop()

lead_ids = [item["lead_id"] for item in items]
selected_id = st.selectbox(
    "Select a prospect",
    lead_ids,
    format_func=lambda value: (
        f"#{value} - "
        + next(
            (
                f"{i['company_name']} ({i.get('contact_name') or 'no contact'})"
                for i in items
                if i["lead_id"] == value
            ),
            "unknown",
        )
    ),
)

refresh = st.checkbox("Re-run the analysis", value=False, key="intelligence_refresh")
col1, col2 = st.columns([1, 4])
load_clicked = col2.button("Load intelligence", type="primary")
col1.caption("Tick to recompute and store a new insight record.")

if load_clicked or "intelligence_payload" not in st.session_state:
    try:
        st.session_state.intelligence_payload = api.get_insights(selected_id, refresh=refresh)
        st.session_state.intelligence_lead_id = selected_id
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load intelligence: {exc}")
        st.session_state.pop("intelligence_payload", None)

payload = st.session_state.get("intelligence_payload")
if not payload or st.session_state.get("intelligence_lead_id") != selected_id:
    st.stop()

if payload.get("is_cached"):
    st.caption("Showing the most recently stored analysis for this lead.")

profile = payload.get("company_profile", {})
score = payload.get("qualification_score", {})

st.subheader(f"{profile.get('company_name', 'Unknown company')}")
meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
meta_col1.metric("Industry", profile.get("industry") or "Not recorded")
meta_col2.metric("Contact", profile.get("contact_name") or "Not recorded")
meta_col3.metric("Status", profile.get("lead_status") or "Not recorded")
meta_col4.metric(
    "Data completeness", f"{profile.get('data_completeness', 0) * 100:.0f}%"
)

st.subheader("Qualification score")
score_col1, score_col2 = st.columns([1, 3])
score_col1.metric("Score", f"{score.get('score', 0):.0f} / 100")
score_col1.metric("Band", score.get("band", "n/a"))
score_col2.caption(score.get("disclaimer", ""))
score_col2.caption(f"Methodology: {score.get('methodology', 'n/a')}")

factors = score.get("factors", [])
if factors:
    st.dataframe(
        pd.DataFrame(factors),
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No factor breakdown is stored for this analysis run.")

left, right = st.columns(2)

with left:
    st.subheader("Business needs")
    for need in payload.get("business_needs", []):
        st.markdown(f"- {need}")

    st.subheader("Sales opportunities")
    for opportunity in payload.get("opportunities", []):
        st.markdown(f"- {opportunity}")

with right:
    st.subheader("Key insights")
    for insight in payload.get("key_insights", []):
        st.markdown(f"- {insight}")

    st.subheader("Information gaps")
    gaps = payload.get("information_gaps", [])
    if gaps:
        for gap in gaps:
            st.markdown(f"- {gap}")
    else:
        st.markdown("- None recorded.")
