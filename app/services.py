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
    needs = next((hint for key, hint in INDUSTRY_HINTS.items() if key in industry), "process efficiency, visibility, and measurable business outcomes")
    opportunities = []
    if float(lead.get("engagement_score") or 0) >= 60:
        opportunities.append("Engagement is promising; follow up with a specific use case.")
    if not opportunities:
        opportunities.append("Ask discovery questions about the problem, urgency, budget, and buying process.")
    return {"company_name": lead.get("company_name", "Unknown"), "industry": lead.get("industry", "Unknown"), "company_summary": f"{lead.get('company_name', 'The company')} is recorded as an organisation in the {lead.get('industry', 'Unknown')} industry.", "potential_needs": needs, "opportunities": opportunities, "source_note": "Insights are inferred from user-supplied lead fields; company facts have not been independently verified."}


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
    fit_score = 0
    if company_size >= 500:
        points += 25; fit_score += 25
        factors.append({"factor": "Large enterprise (500+)", "points": 25})
    elif company_size >= 200:
        points += 20; fit_score += 20
        factors.append({"factor": "Mid-large company (200-499)", "points": 20})
    elif company_size >= 100:
        points += 15; fit_score += 15
        factors.append({"factor": "Medium company (100-199)", "points": 15})
    elif company_size >= 50:
        points += 10; fit_score += 10
        factors.append({"factor": "Small-mid company (50-99)", "points": 10})
    elif company_size >= 10:
        points += 5; fit_score += 5
        factors.append({"factor": "Small company (10-49)", "points": 5})
    if industry not in ("unknown", "", "other"):
        points += 10; fit_score += 10
        factors.append({"factor": "Industry identified", "points": 10})
    intent_score = 0
    if status in ("Qualified", "Proposal", "Negotiation"):
        points += 20; intent_score += 20
        factors.append({"factor": "Advanced lead status", "points": 20})
    elif status == "Contacted":
        points += 10; intent_score += 10
        factors.append({"factor": "Contacted", "points": 10})
    elif status == "New":
        points += 5; intent_score += 5
        factors.append({"factor": "New lead", "points": 5})
    decision_readiness = 0
    if status in ("Proposal", "Negotiation"):
        decision_readiness += 15; points += 15
    elif status == "Qualified":
        decision_readiness += 10; points += 10
    score = min(points, 100)
    tier = "High" if score >= 60 else "Low"
    engagement_comp = min(int(engagement), 100)
    conversion_probability = min(int((engagement_comp * 0.3 + fit_score * 0.25 + intent_score * 0.25 + decision_readiness * 0.2)), 100)
    recommendations = {"High": "Prioritise a personalised follow-up and propose a discovery call immediately.", "Low": "Nurture with educational content and re-engage when activity increases."}
    return {"lead_score": score, "qualification_tier": tier, "conversion_probability": conversion_probability, "probability_components": {"engagement": engagement_comp, "fit": fit_score, "intent": intent_score, "decision_readiness": decision_readiness}, "probability_note": "Conversion probability calculated using engagement, fit, intent, and decision readiness; stored in lead_scores table.", "scoring_method": "Explainable rule-based baseline; not a trained machine-learning model.", "factors": factors, "recommendation": recommendations[tier]}


def next_best_action(lead: dict[str, Any], score_data: dict[str, Any]) -> dict[str, Any]:
    engagement = float(lead.get("engagement_score") or 0)
    status = (lead.get("lead_status") or "New")
    score = int(score_data.get("lead_score") or 0)
    conv_prob = score
    
    if conv_prob >= 70:
        timing = "Within 1-2 days (Priority)"
        channel = ["Email (Personalized)", "Phone Call", "LinkedIn Message"]
        content = ["Case study relevant to industry", "ROI calculator/proposal draft", "Demo invitation"]
        action = "Schedule discovery/demo call with decision maker"
        priority = "High"
    elif conv_prob >= 40:
        timing = "Within 4-5 days"
        channel = ["Email (Nurture)", "LinkedIn Message"]
        content = ["Industry-specific insights", "Product comparison guide", "Customer testimonial"]
        action = "Follow up with value-add content and qualify needs"
        priority = "Medium"
    else:
        timing = "Within 5-10 days (Nurture)"
        channel = ["Email (Drip campaign)", "Content sharing"]
        content = ["Educational blog post", "Industry report", "Newsletter"]
        action = "Add to nurture sequence and monitor engagement"
        priority = "Low"
    
    if engagement >= 70 and status == "New" and conv_prob < 70:
        timing = "Within 12-24 hours (High urgency)"
        channel = ["Phone Call", "Email (Immediate)"]
        priority = "Medium"
    
    return {
        "timing": timing,
        "channel_mix": channel,
        "content_strategy": content,
        "recommended_action": action,
        "priority_level": priority
    }


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
    name = lead.get("contact_name") or "there"
    company = lead.get("company_name") or "your company"
    industry = lead.get("industry") or "your industry"
    openings = {"professional": f"I am reaching out to learn more about the current priorities at {company}.", "friendly": f"I came across {company} and wanted to introduce myself.", "concise": f"I am contacting you about potential ways to support {company}."}
    body = f"Hi {name},\n\n{openings.get(tone, openings['professional'])} For organisations in {industry}, improving process efficiency and achieving measurable outcomes can be important. I would be glad to understand your priorities and explore whether we may be able to help.\n\nWould you be available to {goal}?\n\nBest regards,\nSales Team"
    return {"subject": f"Exploring priorities at {company}", "body": body, "note": "Draft only. Verify details and personalise before sending; this endpoint does not send email."}

KEY_ACTION_KEYWORDS = ["action", "follow up", "follow-up", "schedule", "send", "review", "call back", "callback", "next step", "demo", "proposal", "contract", "trial", "meeting", "email", "provide", "share", "connect"]

def summarize_conversation(transcript: str, meeting_type: str = "Discovery Call") -> dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        try:
            prompt = f"""Summarize this {meeting_type} sales call transcript and extract action items. Return JSON with keys: summary, key_points (list), customer_concerns (list), action_items (list of {{task, assignee, due_date}}), next_steps (list).

Transcript:
{transcript}"""
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json={"model":"openai/gpt-oss-20b","messages":[{"role":"user","content":prompt}],"temperature":0.3}, timeout=30)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            import json as _json
            import re as _re_json
            cleaned = content.strip()
            cleaned = _re_json.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = _re_json.sub(r"\s*```$", "", cleaned)
            if not cleaned.startswith("{"):
                m = _re_json.search(r"\{.*\}", cleaned, _re_json.S)
                if m:
                    cleaned = m.group(0)
            try:
                parsed = _json.loads(cleaned)
            except Exception:
                parsed = {"summary": content, "key_points": [], "customer_concerns": [], "action_items": [], "next_steps": []}
            return {"summary": parsed.get("summary", ""), "key_points": parsed.get("key_points", []), "customer_concerns": parsed.get("customer_concerns", []), "action_items": parsed.get("action_items", []), "next_steps": parsed.get("next_steps", []), "note": "Generated via Groq."}
        except Exception:
            pass
    # Rule-based fallback
    import re as _re
    raw = _re.split(r"(?<=[.!?])\s+|\n+", transcript)
    sentences = [s.strip(" -\t") for s in raw if len(s.strip()) > 12]
    lower = transcript.lower()
    discussion_cues = ["need", "want", "require", "currently", "problem", "challenge", "pain",
                       "goal", "budget", "timeline", "deadline", "competitor", "integrat",
                       "concern", "issue", "cost", "price", "pricing", "plan", "objective"]
    action_cues = ["will", "can you", "please", "follow up", "follow-up", "schedule", "send",
                   "review", "call back", "callback", "next step", "demo", "proposal",
                   "contract", "trial", "meeting", "provide", "share", "connect", "confirm"]
    key_points = [s for s in sentences if any(c in s.lower() for c in discussion_cues)][:6]
    if not key_points:
        key_points = sentences[:3]
    action_items = []
    seen_tasks = set()
    for s in sentences:
        low = s.lower()
        if any(c in low for c in action_cues):
            assignee = "Prospect" if ("prospect:" in low or "customer:" in low or "client:" in low) else "Sales Rep"
            due = "Within 3 business days"
            if "friday" in low: due = "By Friday"
            elif "tomorrow" in low: due = "Tomorrow"
            elif "next week" in low: due = "Next week"
            elif "today" in low: due = "Today"
            task = s.strip()
            if task.lower() in seen_tasks:
                continue
            seen_tasks.add(task.lower())
            action_items.append({"task": task, "assignee": assignee, "due_date": due})
    action_items = action_items[:8]
    if not action_items:
        action_items.append({"task": "Review call notes and send follow-up email", "assignee": "Sales Rep", "due_date": "Within 2 business days"})
    concerns = []
    if "budget" in lower or "cost" in lower or "price" in lower: concerns.append("Budget / pricing discussion")
    if "timeline" in lower or "deadline" in lower: concerns.append("Timeline / deadline mentioned")
    if "competitor" in lower or "alternative" in lower: concerns.append("Competitor mentioned")
    if "integrat" in lower: concerns.append("Integration requirement")
    if "security" in lower or "privacy" in lower or "compliance" in lower: concerns.append("Security / compliance concern")
    next_steps = []
    if "demo" in lower: next_steps.append("Schedule product demo")
    if "proposal" in lower: next_steps.append("Send proposal")
    if "pilot" in lower: next_steps.append("Plan pilot rollout")
    if not next_steps: next_steps.append("Send summary email and schedule next call")
    summary = (f"{meeting_type} with {len(sentences)} key statements. "
               f"Main themes: " + "; ".join(key_points[:3]) if key_points else f"{meeting_type} call summary based on {len(sentences)} statements.")
    return {"summary": summary, "key_points": key_points, "customer_concerns": concerns,
            "action_items": action_items, "next_steps": next_steps,
            "note": "Rule-based extraction (no Groq key or API unavailable)."}
