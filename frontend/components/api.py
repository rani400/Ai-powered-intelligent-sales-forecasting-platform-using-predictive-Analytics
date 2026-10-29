"""All UI/backend interaction passes through HTTP. No direct DB access in UI."""

import os
import requests
import streamlit as st

API_URL = os.getenv(
    'SALES_API_URL',
    'http://127.0.0.1:8000'
).rstrip('/')


class ApiError(Exception):
    pass


def call(method, path, **kwargs):
    try:
        # Allow more time for Gemini AI email generation
        timeout = 120 if path.startswith('/api/outreach') else 25

        response = requests.request(
            method,
            API_URL + path,
            timeout=timeout,
            **kwargs
        )

    except requests.RequestException as exc:
        raise ApiError(
            f'Backend unavailable at {API_URL}. '
            f'Start run_backend.bat first. ({exc})'
        ) from exc

    if not response.ok:
        try:
            body = response.json()
            detail = body.get('detail', body)

            if isinstance(detail, list):
                detail = '; '.join(
                    f'{".".join(map(str, e.get("loc", [])))}: '
                    f'{e.get("msg", "invalid")}'
                    for e in detail
                )

        except ValueError:
            detail = response.text[:240]

        raise ApiError(
            f'HTTP {response.status_code}: {detail}'
        )

    return response.json() if response.content else None


def get_leads(page_size=100):
    return call(
        'GET',
        '/api/leads',
        params={'page_size': page_size}
    )['items']


def lead_picker(key='selected_lead'):
    try:
        leads = get_leads()

    except ApiError as exc:
        st.error(str(exc))
        st.stop()

    if not leads:
        st.info(
            'No leads yet. Add your first prospect in Lead Management.'
        )
        st.stop()

    ids = [lead['lead_id'] for lead in leads]

    name_map = {
        l['lead_id']:
        f"{l['company_name']} · "
        f"{l.get('contact_name') or 'Contact not added'} "
        f"(#{l['lead_id']})"
        for l in leads
    }

    chosen = st.selectbox(
        'Select prospect',
        ids,
        format_func=lambda x: name_map[x],
        key=key
    )

    return next(
        l for l in leads
        if l['lead_id'] == chosen
    )


def show_factors(items):
    for item in items:
        left, right = st.columns([4, 1])

        with left:
            st.markdown(f"**{item['name']}**")
            st.caption(item['explanation'])

        with right:
            st.markdown(
                f"**{item['points']:g} / "
                f"{item['max_points']:g}**"
            )

        st.progress(
            min(
                1.0,
                max(
                    0.0,
                    item['points'] / item['max_points']
                )
            )
        )