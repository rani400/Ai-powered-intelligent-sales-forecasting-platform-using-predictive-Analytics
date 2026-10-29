"""Evidence-bounded company insights and transparent RULE-BASED qualification."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import CompanyInsight, Lead

INDUSTRY_IDEAS = {
    'technology': ('Technology organizations often evaluate tools for workflow efficiency and scalable operations.',
                   'Explore workflow automation needs', 'Offer a demonstration aligned with their current stack'),
    'healthcare': ('Healthcare organizations may prioritize operational consistency, privacy and process efficiency.',
                   'Clarify applicable compliance and workflow requirements', 'Explore approved process-improvement opportunities'),
    'retail': ('Retail organizations may benefit from demand visibility, inventory coordination and customer engagement.',
               'Ask about inventory and customer experience priorities', 'Discuss forecasting or customer-engagement use cases'),
    'finance': ('Financial service teams often prioritize compliance, auditability and process efficiency.',
                'Understand review and compliance constraints', 'Explore auditable workflow tools'),
    'manufacturing': ('Manufacturing teams often focus on throughput, process coordination and supply chain visibility.',
                      'Ask about demand planning and procurement priorities', 'Discuss process visibility opportunities'),
    'education': ('Education organizations can evaluate accessibility, administration and learner support tools.',
                  'Determine administrative workflow priorities', 'Explore lightweight process automation'),
}


def qualification(lead: Lead):
    status_pts = {'New': 3, 'Contacted': 7, 'Qualified': 13, 'Converted': 15}.get(lead.lead_status, 0)
    values = [
        ('Industry identified', 15 if lead.industry else 0, 15, 'Industry is provided' if lead.industry else 'Industry is missing'),
        ('Named contact', 10 if lead.contact_name else 0, 10, 'Contact is named' if lead.contact_name else 'Contact not identified'),
        ('Email available', 20 if lead.email else 0, 20, 'Email supplied' if lead.email else 'No email supplied'),
        ('Phone available', 10 if lead.phone else 0, 10, 'Phone supplied' if lead.phone else 'No phone supplied'),
        ('Company size available', 10 if lead.company_size else 0, 10, 'Size supplied' if lead.company_size else 'Size not recorded'),
        ('Engagement', round(lead.engagement_score * .20, 2), 20, f'Engagement input: {lead.engagement_score}/100'),
        ('Lifecycle', status_pts, 15, f'Stage: {lead.lead_status}'),
    ]
    factors = [{'name': n, 'points': p, 'max_points': m, 'explanation': e} for n, p, m, e in values]
    score = round(sum(x['points'] for x in factors), 2)
    band = 'Very High' if score >= 80 else 'High' if score >= 60 else 'Medium' if score >= 40 else 'Low' if score >= 20 else 'Very Low'
    return score, band, factors


def analyze(db: Session, lead: Lead):
    industry = (lead.industry or '').lower().strip()
    context, need, opportunity = INDUSTRY_IDEAS.get(industry, (
        'Specific industry practices have not been verified; discuss the prospect’s workflow and goals directly.',
        'Clarify current operational priorities', 'Identify a relevant use case with the prospect'))
    summary_parts = [f'{lead.company_name} is a recorded sales prospect.']
    if lead.industry:
        summary_parts.append(f'Its supplied industry is {lead.industry}.')
    if lead.company_size:
        summary_parts.append(f'Recorded company-size category: {lead.company_size}.')
    summary_parts.append('No external company research was performed; this summary uses submitted lead data only.')
    observations = [f'Current lead stage: {lead.lead_status}', f'Recorded engagement: {lead.engagement_score:.0f}/100']
    if lead.contact_name:
        observations.append(f'Named contact: {lead.contact_name}')
    if lead.source:
        observations.append(f'Lead source recorded: {lead.source}')
    gaps = []
    for attr, message in [
        ('industry', 'Industry not recorded'), ('contact_name', 'Contact name not recorded'),
        ('email', 'Email not recorded'), ('phone', 'Phone not recorded'),
        ('company_size', 'Company size not recorded')]:
        if not getattr(lead, attr):
            gaps.append(message)
    gaps.append('Revenue, funding, headcount and market share have not been independently verified')
    score, band, factors = qualification(lead)
    insight = CompanyInsight(
        lead_id=lead.lead_id, company_summary=' '.join(summary_parts), industry_context=context,
        potential_needs=[need], potential_opportunities=[opportunity], observations=observations,
        information_gaps=gaps, qualification_score=score, qualification_band=band,
        contributing_factors=factors,
        methodology='Rule-based 0–100 qualification: industry 15, name 10, email 20, phone 10, size 10, engagement 20, stage 15. Not a trained ML score.')
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


def latest(db: Session, lead_id: int):
    return db.scalars(select(CompanyInsight).where(CompanyInsight.lead_id == lead_id)
                      .order_by(CompanyInsight.created_at.desc(), CompanyInsight.insight_id.desc())).first()
