"""Leads page - import, search, add, edit and delete prospect records."""

from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

from api_client import ApiError, SalesGenieApi  # noqa: E402

LEAD_STATUSES = ["New", "Contacted", "Qualified", "Unqualified", "Converted", "Lost"]
COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]

st.set_page_config(page_title="Leads - SalesGenie AI", page_icon="SG", layout="wide")

api = SalesGenieApi(st.session_state.get("api_base_url"))


def show_error(exc: Exception) -> None:
    """Render an error message that names the actual backend failure."""
    if isinstance(exc, ApiError):
        st.error(exc.message)
    else:
        st.error(f"Request failed: {exc}")


def load_leads() -> dict | None:
    """Fetch the lead list using the current filters."""
    search = st.session_state.get("leads_search", "") or None
    status_filter = st.session_state.get("leads_status", "") or None
    industry = st.session_state.get("leads_industry", "") or None
    try:
        return api.list_leads(search=search, status=status_filter, industry=industry)
    except Exception as exc:  # noqa: BLE001
        show_error(exc)
        return None


def render_import() -> None:
    """Render the CSV upload panel and the import report."""
    st.subheader("Import leads from CSV")
    st.caption(
        "Required columns: company_name, email. "
        "Optional: industry, contact_name, phone, lead_status, company_size, notes."
    )
    uploaded = st.file_uploader("CSV file", type=["csv"], key="leads_upload")
    policy = st.radio(
        "Duplicate policy",
        ["reject", "skip"],
        horizontal=True,
        key="leads_duplicate_policy",
        help="'reject' reports duplicates as rejected rows; 'skip' reports them without failing.",
    )

    if st.button("Import CSV", type="primary", disabled=uploaded is None):
        if uploaded is None:
            st.warning("Choose a CSV file first.")
        else:
            try:
                report = api.import_leads(
                    uploaded.getvalue(), uploaded.name, duplicate_policy=policy
                )
                st.success(
                    f"Imported {report.get('inserted', 0)} of {report.get('total_rows', 0)} rows."
                )
                col1, col2, col3 = st.columns(3)
                col1.metric("Inserted", report.get("inserted", 0))
                col2.metric("Duplicates", report.get("duplicates", 0))
                col3.metric("Rejected", report.get("rejected", 0))
                errors = report.get("errors") or []
                if errors:
                    st.warning(f"{len(errors)} row(s) were not imported.")
                    st.dataframe(
                        pd.DataFrame(errors),
                        width="stretch",
                        hide_index=True,
                    )
            except Exception as exc:  # noqa: BLE001
                show_error(exc)


def render_add_form() -> None:
    """Render the manual Add Lead form."""
    st.subheader("Add a lead")
    with st.form("add_lead_form", clear_on_submit=True):
        company_name = st.text_input("Company name *")
        col1, col2 = st.columns(2)
        industry = col1.text_input("Industry")
        company_size = col2.selectbox("Company size", [""] + COMPANY_SIZES)
        contact_name = st.text_input("Contact name")
        col3, col4 = st.columns(2)
        email = col3.text_input("Email")
        phone = col4.text_input("Phone")
        lead_status = st.selectbox("Lead status", LEAD_STATUSES)
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Create lead", type="primary")

    if submitted:
        payload = {
            "company_name": company_name.strip(),
            "industry": industry.strip() or None,
            "contact_name": contact_name.strip() or None,
            "email": email.strip() or None,
            "phone": phone.strip() or None,
            "lead_status": lead_status,
            "notes": notes.strip() or None,
        }
        if company_size:
            payload["company_size"] = company_size
        try:
            created = api.create_lead(payload)
            st.success(f"Created lead {created['lead_id']} - {created['company_name']}.")
        except Exception as exc:  # noqa: BLE001
            show_error(exc)


def render_lead_table(payload: dict) -> None:
    """Render the lead table with edit and delete controls."""
    st.subheader(f"Leads ({payload['total']})")
    items = payload.get("items", [])
    if not items:
        st.info("No leads match the current filters.")
        return

    frame = pd.DataFrame(items)
    display_columns = [
        "lead_id",
        "company_name",
        "industry",
        "contact_name",
        "email",
        "phone",
        "lead_status",
        "company_size",
        "source",
    ]
    st.dataframe(
        frame[[column for column in display_columns if column in frame.columns]],
        width="stretch",
        hide_index=True,
    )

    lead_ids = [item["lead_id"] for item in items]
    selected_id = st.selectbox(
        "Select a lead to edit or delete",
        lead_ids,
        format_func=lambda value: f"#{value} - {next(i['company_name'] for i in items if i['lead_id'] == value)}",
        key="leads_selected",
    )
    selected = next(item for item in items if item["lead_id"] == selected_id)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Edit lead")
        with st.form(f"edit_lead_{selected_id}"):
            new_company = st.text_input("Company name", value=selected["company_name"])
            new_industry = st.text_input("Industry", value=selected.get("industry") or "")
            new_contact = st.text_input("Contact name", value=selected.get("contact_name") or "")
            new_email = st.text_input("Email", value=selected.get("email") or "")
            new_phone = st.text_input("Phone", value=selected.get("phone") or "")
            new_status = st.selectbox(
                "Lead status",
                LEAD_STATUSES,
                index=LEAD_STATUSES.index(selected["lead_status"])
                if selected["lead_status"] in LEAD_STATUSES
                else 0,
            )
            new_size = st.selectbox(
                "Company size",
                [""] + COMPANY_SIZES,
                index=COMPANY_SIZES.index(selected["company_size"]) + 1
                if selected.get("company_size") in COMPANY_SIZES
                else 0,
            )
            new_notes = st.text_area("Notes", value=selected.get("notes") or "")
            edit_submitted = st.form_submit_button("Save changes")

        if edit_submitted:
            payload = {
                "company_name": new_company.strip(),
                "industry": new_industry.strip() or None,
                "contact_name": new_contact.strip() or None,
                "email": new_email.strip() or None,
                "phone": new_phone.strip() or None,
                "lead_status": new_status,
                "notes": new_notes.strip() or None,
                "company_size": new_size or None,
            }
            try:
                api.update_lead(selected_id, payload)
                st.success(f"Lead {selected_id} updated.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                show_error(exc)

    with right:
        st.markdown("#### Delete lead")
        st.warning(
            "Deleting a lead also removes its stored insights, scores and outreach drafts."
        )
        confirm = st.checkbox("I understand this cannot be undone", key="leads_delete_confirm")
        if st.button("Delete lead", type="secondary", disabled=not confirm):
            try:
                api.delete_lead(selected_id)
                st.success(f"Lead {selected_id} deleted.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                show_error(exc)


st.title("Leads")
st.write("Import, search and maintain the prospect database.")

if not api.is_reachable():
    st.error(
        "The backend is not reachable. Start it with "
        "`python -m uvicorn app.main:app --app-dir backend`."
    )
    st.stop()

filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
filter_col1.text_input(
    "Search company, contact or email", key="leads_search", placeholder="Type to filter..."
)
filter_col2.selectbox("Status", [""] + LEAD_STATUSES, key="leads_status")
filter_col3.text_input("Industry", key="leads_industry")

st.divider()

import_col, add_col = st.columns(2)
with import_col:
    render_import()
with add_col:
    render_add_form()

st.divider()

payload = load_leads()
if payload is not None:
    render_lead_table(payload)
