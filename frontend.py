import os
import requests
import streamlit as st

API_BASE = os.getenv("SALESGENIE_API", "http://127.0.0.1:8000")
st.set_page_config(page_title="SalesGenie AI", page_icon="🎯", layout="wide")
st.title("🎯 SalesGenie AI")
st.caption("Lead Management · Lead Intelligence · AI Outreach · Lead Scoring")

@st.cache_data(ttl=3)
def get_leads(search="", status=""):
    params = {}
    if search.strip(): params["search"] = search.strip()
    if status and status != "All": params["status"] = status
    response = requests.get(f"{API_BASE}/leads", params=params, timeout=8)
    response.raise_for_status()
    return response.json()

def api_error(error):
    st.error(f"Could not reach the backend API at {API_BASE}. Start it in a separate terminal first. Details: {error}")

try:
    health = requests.get(f"{API_BASE}/health", timeout=2)
    health.raise_for_status()
except Exception as exc:
    st.warning("Backend API is not running yet. Start it using the instructions in README.md.")
    st.code(".\\.venv312\\Scripts\\python.exe -m uvicorn app.main:app --reload")
    st.stop()

pages = ["Lead Management", "Lead Intelligence", "AI Outreach", "Lead Scoring"]
page = st.sidebar.radio("Choose module", pages)
st.sidebar.caption("This app implements only the four requested modules.")

if page == "Lead Management":
    st.header("1. Lead Management")
    with st.expander("➕ Add a new lead", expanded=False):
        with st.form("create_lead"):
            c1, c2, c3 = st.columns(3)
            company = c1.text_input("Company name *")
            industry = c2.selectbox("Industry", ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Education", "Other"])
            contact = c3.text_input("Contact name", "there")
            title = c1.text_input("Contact title")
            email = c2.text_input("Email")
            phone = c3.text_input("Phone")
            size = c1.number_input("Company size (employees)", min_value=0, value=0)
            engagement = c2.slider("Engagement score", 0, 100, 0)
            status = c3.selectbox("Lead status", ["New", "Contacted", "Qualified", "Proposal", "Negotiation", "Won", "Lost"])
            notes = st.text_area("Notes / known business needs")
            submitted = st.form_submit_button("Save lead", type="primary")
            if submitted:
                if not company.strip():
                    st.error("Company name is required.")
                else:
                    payload = {"company_name": company.strip(), "industry": industry, "contact_name": contact.strip() or "there", "contact_title": title, "email": email or None, "phone": phone or None, "company_size": int(size), "engagement_score": engagement, "lead_status": status, "notes": notes}
                    try:
                        r = requests.post(f"{API_BASE}/leads", json=payload, timeout=8); r.raise_for_status()
                        st.cache_data.clear(); st.success(f"Lead saved (ID {r.json()['id']})."); st.rerun()
                    except Exception as exc: api_error(exc)
                    try:
                        r = requests.post(f"{API_BASE}/leads", json=payload, timeout=8); r.raise_for_status()
                        st.cache_data.clear(); st.success(f"Lead saved (ID {r.json()['id']})."); st.rerun()
                    except Exception as exc: api_error(exc)
    col1, col2, col3 = st.columns([2, 1, 1])
    search = col1.text_input("Search by company, contact, email, or industry")
    filter_status = col2.selectbox("Status filter", ["All", "New", "Contacted", "Qualified", "Proposal", "Negotiation", "Won", "Lost"])
    if col3.button("Refresh leads"):
        st.cache_data.clear()
        st.rerun()
    
    with st.expander("📁 Import leads from CSV", expanded=False):
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            if st.button("Import CSV"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                    r = requests.post(f"{API_BASE}/leads/import", files=files, timeout=30)
                    r.raise_for_status()
                    result = r.json()
                    st.cache_data.clear()
                    if result["inserted"] > 0:
                        st.success(f"Successfully imported {result['inserted']} lead(s).")
                    if result["errors"]:
                        st.warning(f"{len(result['errors'])} error(s) occurred:")
                        for err in result["errors"][:10]:
                            st.text(err)
                    st.rerun()
                except Exception as exc:
                    api_error(exc)
        st.caption("CSV should have columns: company_name, industry, contact_name, contact_title, email, phone, company_size, engagement_score, website_visits, email_opens, email_clicks, budget_confirmed, need_identified, decision_maker, lead_status, notes")
    
    try:
        leads = get_leads(search, filter_status)
        st.write(f"**{len(leads)} lead(s)**")
        if leads:
            st.dataframe([{ "ID": x["id"], "Company": x["company_name"], "Industry": x["industry"], "Contact": x["contact_name"], "Email": x["email"], "Status": x["lead_status"], "Engagement": x["engagement_score"] } for x in leads], width='stretch', hide_index=True)
            ids = [x["id"] for x in leads]
            chosen_id = st.selectbox("Select lead to update or delete", ids, format_func=lambda i: f"#{i} — {next((x['company_name'] for x in leads if x['id']==i), '')}")
            chosen = next(x for x in leads if x["id"] == chosen_id)
            with st.expander("Edit selected lead"):
                with st.form("edit_lead"):
                    new_status = st.selectbox("Status", ["New", "Contacted", "Qualified", "Proposal", "Negotiation", "Won", "Lost"], index=["New", "Contacted", "Qualified", "Proposal", "Negotiation", "Won", "Lost"].index(chosen["lead_status"]) if chosen["lead_status"] in ["New", "Contacted", "Qualified", "Proposal", "Negotiation", "Won", "Lost"] else 0)
                    new_engagement = st.slider("Engagement score", 0, 100, int(chosen["engagement_score"]))
                    new_notes = st.text_area("Notes", chosen["notes"])
                    save_edit = st.form_submit_button("Update lead")
                    if save_edit:
                        try:
                            r = requests.patch(f"{API_BASE}/leads/{chosen_id}", json={"lead_status": new_status, "engagement_score": new_engagement, "notes": new_notes}, timeout=8); r.raise_for_status()
                            st.cache_data.clear(); st.success("Lead updated."); st.rerun()
                        except Exception as exc: api_error(exc)
            if st.button("Delete selected lead", type="secondary"):
                try:
                    r = requests.delete(f"{API_BASE}/leads/{chosen_id}", timeout=8); r.raise_for_status()
                    st.cache_data.clear(); st.success("Lead deleted."); st.rerun()
                except Exception as exc: api_error(exc)
        else: st.info("No leads found. Add a lead above or import sample data through the API.")
    except Exception as exc: api_error(exc)

elif page == "Lead Intelligence":
    st.header("2. Lead Intelligence")
    st.write("Review potential business needs and opportunities inferred from lead information.")
    try:
        leads = get_leads()
        if not leads: st.info("Add a lead in Lead Management first.")
        else:
            lead_id = st.selectbox("Choose lead", [x["id"] for x in leads], format_func=lambda i: f"{next(x['company_name'] for x in leads if x['id']==i)} (ID {i})", key="intel_id")
            if st.button("Analyze company", type="primary"):
                r = requests.get(f"{API_BASE}/leads/{lead_id}/intelligence", timeout=10); r.raise_for_status(); result = r.json()
                a = result["company_analysis"]; s = result["lead_scoring"]
                st.subheader(a["company_name"])
                st.write(a["company_summary"])
                st.metric("Qualification score", f"{s['lead_score']}/100", s["qualification_tier"] + " priority")
                st.markdown("**Potential needs**"); st.write(a["potential_needs"])
                st.markdown("**Potential opportunities**")
                for item in a["opportunities"]: st.write("• " + item)
                st.caption(a["source_note"])
    except Exception as exc: api_error(exc)

elif page == "AI Outreach":
    st.header("3. AI Outreach")
    st.write("Create a personalised email draft. Review all details before sending; this app does not send emails.")
    try:
        leads = get_leads()
        if not leads: st.info("Add a lead in Lead Management first.")
        else:
            lead_id = st.selectbox("Choose prospect", [x["id"] for x in leads], format_func=lambda i: f"{next(x['company_name'] for x in leads if x['id']==i)} (ID {i})", key="outreach_id")
            tone = st.selectbox("Tone", ["professional", "friendly", "concise"])
            goal = st.text_input("Email goal", "schedule a 15-minute discovery call")
            if st.button("Generate email draft", type="primary"):
                r = requests.post(f"{API_BASE}/leads/{lead_id}/outreach", json={"tone": tone, "goal": goal}, timeout=10); r.raise_for_status(); draft = r.json()
                st.text_input("Subject", draft["subject"])
                st.text_area("Email body", draft["body"], height=280)
                st.caption(draft["note"])
    except Exception as exc: api_error(exc)

elif page == "Lead Scoring":
    st.header("4. Lead Scoring")
    st.write("Review a transparent 0–100 qualification score and its contributing factors.")
    try:
        leads = get_leads()
        if not leads: st.info("Add a lead in Lead Management first.")
        else:
            lead_id = st.selectbox("Choose lead", [x["id"] for x in leads], format_func=lambda i: f"{next(x['company_name'] for x in leads if x['id']==i)} (ID {i})", key="score_id")
            if st.button("Calculate lead score", type="primary"):
                r = requests.get(f"{API_BASE}/leads/{lead_id}/score", timeout=10); r.raise_for_status(); result = r.json()
                st.metric("Lead qualification score", f"{result['lead_score']}/100", result["qualification_tier"] + " priority")
                st.progress(result["lead_score"] / 100)
                st.markdown("**Scoring factors**")
                if result["factors"]: st.dataframe(result["factors"], width='stretch', hide_index=True)
                else: st.info("No positive scoring factors were identified yet.")
                st.markdown("**Recommended next action**")
                st.write(result["recommendation"])
                st.warning(result["scoring_method"] + " " + result["probability_note"])
    except Exception as exc: api_error(exc)
