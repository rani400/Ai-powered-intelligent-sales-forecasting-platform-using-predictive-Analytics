"""SalesGenie AI - Streamlit application entry point.

Run from the project root:

    python -m streamlit run frontend/app.py

The interface is split across three pages:

* **Leads** - import, search, add, edit and delete prospect records.
* **Intelligence** - company profile, qualification score, opportunities and gaps for a lead.
* **Outreach** - generate, preview and store a personalised first-touch email draft.
"""

from __future__ import annotations

import os
import sys

import streamlit as st

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(FRONTEND_DIR)
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

from api_client import ApiError, SalesGenieApi  # noqa: E402

st.set_page_config(
    page_title="SalesGenie AI",
    page_icon="SG",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_api() -> SalesGenieApi:
    """Return a cached API client bound to the configured base URL."""
    base_url = st.session_state.get("api_base_url") or os.getenv(
        "API_BASE_URL", "http://127.0.0.1:8000"
    )
    if "api_client" not in st.session_state:
        st.session_state.api_client = SalesGenieApi(base_url)
    else:
        st.session_state.api_client.base_url = base_url.rstrip("/")
    return st.session_state.api_client


def main() -> None:
    """Render the application shell."""
    api = get_api()

    with st.sidebar:
        st.title("SalesGenie AI")
        st.caption("AI Sales Assistant & Lead Intelligence Platform")

        base_url = st.text_input(
            "Backend URL",
            value=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
            help="Base URL of the FastAPI backend.",
        )
        if base_url != st.session_state.get("api_base_url"):
            st.session_state.api_base_url = base_url
            st.session_state.pop("api_client", None)

        if st.button("Check connection", width="stretch"):
            try:
                api = get_api()
                health = api.health()
                st.success(f"Backend reachable - {health.get('service')} v{health.get('version')}")
            except ApiError as exc:
                st.error(f"Backend error: {exc}")
            except Exception as exc:  # noqa: BLE001 - surface any connection problem
                st.error(f"Cannot reach the backend: {exc}")

        st.divider()
        st.markdown(
            """
### Milestone 1
Lead management and the intelligence engine are implemented and tested.

### Milestone 2 (first slice)
AI outreach generation with prompt templates and draft storage.

### Not in this release
CRM sync, conversation intelligence, the full analytics dashboard and the learned conversion
model are later stages.
"""
        )

    st.title("SalesGenie AI")
    st.write(
        "Manage prospect records, review company intelligence and qualification scores, and "
        "draft first-touch outreach from a single workspace."
    )

    if not api.is_reachable():
        st.error(
            "The backend is not reachable. Start it with "
            "`python -m uvicorn app.main:app --app-dir backend` and reload this page."
        )
        return

    try:
        stats = api.stats()
    except ApiError as exc:
        st.error(f"Could not load dashboard counters: {exc}")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total leads", stats.get("total_leads", 0))
    col2.metric("Scored leads", stats.get("scored_leads", 0))
    average = stats.get("average_score")
    col3.metric("Average score", f"{average:.1f}" if average is not None else "n/a")
    col4.metric("Industries tracked", len(stats.get("by_industry", {})))

    left, right = st.columns(2)
    with left:
        st.subheader("Leads by status")
        by_status = stats.get("by_status", {})
        if by_status:
            st.bar_chart(by_status)
        else:
            st.info("No leads recorded yet - import a CSV from the Leads page.")
    with right:
        st.subheader("Leads by industry")
        by_industry = stats.get("by_industry", {})
        if by_industry:
            st.bar_chart(by_industry)
        else:
            st.info("No industry data recorded yet.")

    st.divider()
    st.subheader("Quick start")
    st.markdown(
        "1. Open **Leads** and upload `data/sample_leads.csv`.\n"
        "2. Open **Intelligence**, pick a lead and review the company analysis and score.\n"
        "3. Open **Outreach**, generate a draft and review it before sending it manually."
    )


if __name__ == "__main__":
    main()
