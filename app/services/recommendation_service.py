"""Transparent prioritized next-best-action recommendations."""


def recommend(lead, score: float, probability: float | None):
    if not lead.email and not lead.phone:
        return {'recommended_action': 'Request missing contact details',
                'recommendation_reason': 'The prospect has no recorded reachable email or phone channel.',
                'recommendation_priority': 'High', 'supporting_factors': ['No email', 'No phone'],
                'suggested_outreach_goal': 'Introduction'}
    if lead.lead_status == 'Converted':
        return {'recommended_action': 'Review conversion and coordinate handoff',
                'recommendation_reason': 'The lifecycle stage is already Converted; no unsolicited outreach is recommended.',
                'recommendation_priority': 'Low', 'supporting_factors': ['Converted stage'],
                'suggested_outreach_goal': 'Follow-up'}
    if lead.lead_status == 'Qualified' and (probability is None or probability >= .55):
        return {'recommended_action': 'Schedule a discovery call',
                'recommendation_reason': 'The lead is qualified and merits an explicit discussion of needs and fit.',
                'recommendation_priority': 'High', 'supporting_factors': ['Qualified stage', f'Lead score {score:.0f}/100'],
                'suggested_outreach_goal': 'Discovery call'}
    if lead.lead_status == 'Contacted':
        return {'recommended_action': 'Send a contextual follow-up',
                'recommendation_reason': 'The contact has already been approached; ask a concrete follow-up question.',
                'recommendation_priority': 'High' if score >= 60 else 'Medium',
                'supporting_factors': ['Contacted stage', f'Engagement {lead.engagement_score:.0f}/100'],
                'suggested_outreach_goal': 'Follow-up'}
    if score >= 65:
        return {'recommended_action': 'Prioritize personalized introduction',
                'recommendation_reason': 'Good recorded engagement and profile completeness make a tailored first message appropriate.',
                'recommendation_priority': 'High', 'supporting_factors': [f'Lead score {score:.0f}/100'],
                'suggested_outreach_goal': 'Introduction'}
    if not lead.contact_name or not lead.industry:
        return {'recommended_action': 'Complete prospect research',
                'recommendation_reason': 'Missing profile fields limit personalization and confidence in prioritization.',
                'recommendation_priority': 'Medium', 'supporting_factors': ['Missing industry or named contact'],
                'suggested_outreach_goal': 'Introduction'}
    return {'recommended_action': 'Send a light introduction and continue nurturing',
            'recommendation_reason': 'Lead is early in its lifecycle; a low-pressure introduction is suitable.',
            'recommendation_priority': 'Medium', 'supporting_factors': ['New or low-engagement lead'],
            'suggested_outreach_goal': 'Introduction'}
