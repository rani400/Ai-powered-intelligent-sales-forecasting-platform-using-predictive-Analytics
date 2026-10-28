from typing import Any

INDUSTRY_HINTS = {
    "technology": "automation, scalability, integration, and security",
    "healthcare": "workflow efficiency, privacy, and reliable operations",
    "finance": "risk control, compliance, reporting, and efficiency",
    "retail": "customer experience, inventory visibility, and sales growth",
    "manufacturing": "operational efficiency, downtime reduction, and process visibility",
    "education": "student engagement, administrative efficiency, and reporting",
}

def company_analysis(lead: dict[str, Any]) -> dict[str, Any]:
    industry = (lead.get("industry") or "Unknown").strip().lower()
    needs = next((hint for key, hint in INDUSTRY_HINTS.items() if key in industry),
                 "process efficiency, visibility, and measurable business outcomes")
    opportunities = []
    if float(lead.get("engagement_score") or 0) >= 60 or int(lead.get("email_clicks") or 0) > 0:
        opportunities.append("Engagement is promising; follow up with a specific use case.")
    if lead.get("budget_confirmed"):
        opportunities.append("Discuss scope, decision criteria, and implementation timeline.")
    if lead.get("need_identified"):
        opportunities.append("Connect product value directly to the stated business need.")
    if not opportunities:
        opportunities.append("Ask discovery questions about the problem, urgency, budget, and buying process.")
    return {
        "company_name": lead.get("company_name", "Unknown"),
        "industry": lead.get("industry", "Unknown"),
        "company_summary": f"{lead.get('company_name', 'The company')} is recorded as an organisation in the {lead.get('industry', 'Unknown')} industry.",
        "potential_needs": needs,
        "opportunities": opportunities,
        "source_note": "Insights are inferred from user-supplied lead fields; company facts have not been independently verified."
    }

def score_lead(lead: dict[str, Any]) -> dict[str, Any]:
    points, factors = 0, []
    rules = [
        (float(lead.get("engagement_score") or 0) >= 70, 25, "High engagement"),
        (int(lead.get("email_clicks") or 0) > 0, 10, "Clicked an outreach email"),
        (int(lead.get("email_opens") or 0) >= 2, 5, "Opened emails more than once"),
        (int(lead.get("website_visits") or 0) >= 3, 10, "Repeated website visits"),
        (bool(lead.get("budget_confirmed")), 15, "Budget confirmed"),
        (bool(lead.get("need_identified")), 15, "Business need identified"),
        (bool(lead.get("decision_maker")), 10, "Decision-maker identified"),
        (int(lead.get("company_size") or 0) >= 100, 5, "Company size may support a larger engagement"),
        ((lead.get("industry") or "Unknown").lower() not in ("unknown", "", "other"), 5, "Industry information available"),
    ]
    for condition, weight, label in rules:
        if condition:
            points += weight
            factors.append({"factor": label, "points": weight})
    score = min(points, 100)
    tier = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
    recommendations = {
        "High": "Prioritise a personalised follow-up and propose a discovery call.",
        "Medium": "Share a relevant case study and ask one qualifying question.",
        "Low": "Gather missing information and use a low-pressure nurture message.",
    }
    return {"lead_score": score, "qualification_tier": tier, "conversion_probability": None,
            "probability_note": "A real conversion probability requires historical leads with known outcomes and a validated predictive model.",
            "scoring_method": "Explainable rule-based baseline; not a trained machine-learning model.",
            "factors": factors, "recommendation": recommendations[tier]}

def generate_outreach(lead: dict[str, Any], tone: str = "professional", goal: str = "schedule a short discovery call") -> dict[str, str]:
    name = lead.get("contact_name") or "there"
    company = lead.get("company_name") or "your company"
    industry = lead.get("industry") or "your industry"
    openings = {
        "professional": f"I am reaching out to learn more about the current priorities at {company}.",
        "friendly": f"I came across {company} and wanted to introduce myself.",
        "concise": f"I am contacting you about potential ways to support {company}.",
    }
    body = (f"Hi {name},\n\n{openings.get(tone, openings['professional'])} "
            f"For organisations in {industry}, improving process efficiency and achieving measurable outcomes can be important. "
            f"I would be glad to understand your priorities and explore whether we may be able to help.\n\n"
            f"Would you be available to {goal}?\n\nBest regards,\nSales Team")
    return {"subject": f"Exploring priorities at {company}", "body": body,
            "note": "Draft only. Verify details and personalise before sending; this endpoint does not send email."}
