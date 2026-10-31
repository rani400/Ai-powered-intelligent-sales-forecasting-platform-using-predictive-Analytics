import os
import requests
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
    if float(lead.get("engagement_score") or 0) >= 60:
        opportunities.append("Engagement is promising; follow up with a specific use case.")
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
    engagement = float(lead.get("engagement_score") or 0)
    company_size = int(lead.get("company_size") or 0)
    industry = (lead.get("industry") or "Unknown").lower()
    status = (lead.get("lead_status") or "New")
    
    if engagement >= 90:
        points += 30
        factors.append({"factor": "Very high engagement (90%+)", "points": 30})
    elif engagement >= 70:
        points += 25
        factors.append({"factor": "High engagement (70-89%)", "points": 25})
    elif engagement >= 50:
        points += 18
        factors.append({"factor": "Good engagement (50-69%)", "points": 18})
    elif engagement >= 30:
        points += 12
        factors.append({"factor": "Moderate engagement (30-49%)", "points": 12})
    elif engagement >= 10:
        points += 6
        factors.append({"factor": "Low engagement (10-29%)", "points": 6})
    else:
        points += 0
        factors.append({"factor": "No/minimal engagement (0-9%)", "points": 0})
    
    if company_size >= 500:
        points += 25
        factors.append({"factor": "Large enterprise (500+)", "points": 25})
    elif company_size >= 200:
        points += 20
        factors.append({"factor": "Mid-large company (200-499)", "points": 20})
    elif company_size >= 100:
        points += 15
        factors.append({"factor": "Medium company (100-199)", "points": 15})
    elif company_size >= 50:
        points += 10
        factors.append({"factor": "Small-mid company (50-99)", "points": 10})
    elif company_size >= 10:
        points += 5
        factors.append({"factor": "Small company (10-49)", "points": 5})
    else:
        points += 0
    
    if industry not in ("unknown", "", "other"):
        points += 10
        factors.append({"factor": "Industry identified", "points": 10})
    
    if status == "Won":
        points += 25
        factors.append({"factor": "Won status", "points": 25})
    elif status == "Negotiation":
        points += 20
        factors.append({"factor": "Negotiation stage", "points": 20})
    elif status == "Proposal":
        points += 18
        factors.append({"factor": "Proposal stage", "points": 18})
    elif status == "Qualified":
        points += 15
        factors.append({"factor": "Qualified", "points": 15})
    elif status == "Contacted":
        points += 8
        factors.append({"factor": "Contacted", "points": 8})
    elif status == "New":
        points += 3
        factors.append({"factor": "New lead", "points": 3})
    elif status == "Lost":
        points += 0
        factors.append({"factor": "Lost status", "points": 0})
    
    score = min(points, 100)
    if score >= 60:
        tier = "High"
    else:
        tier = "Low"
    
    recommendations = {
        "High": "Prioritise a personalised follow-up and propose a discovery call immediately.",
        "Low": "Nurture with educational content and re-engage when activity increases.",
    }
    return {"lead_score": score, "qualification_tier": tier, "conversion_probability": None,
            "probability_note": "A real conversion probability requires historical leads with known outcomes and a validated predictive model.",
            "scoring_method": "Explainable rule-based baseline; not a trained machine-learning model.",
            "factors": factors, "recommendation": recommendations[tier]}

import os
import requests

# ... keep rest

def generate_outreach(lead, tone="professional", goal="schedule a short discovery call"):
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        try:
            name = lead.get("contact_name") or "there"
            company = lead.get("company_name") or "your company"
            industry = lead.get("industry") or "your industry"
            prompt = f"Write a {tone} outreach email to {name} at {company} ({industry}) with goal: {goal}. Return subject and body."
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json={"model":"openai/gpt-oss-20b","messages":[{"role":"user","content":prompt}]}, timeout=20)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            return {"subject": f"Exploring priorities at {company}", "body": content, "note": "Generated via Groq. Draft only."}
        except Exception:
            pass
    # fallback template (original)
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

