"""AI outreach generation service and prompt templates (Module 3).

The service talks to any OpenAI-compatible chat-completions endpoint. When no provider key is
configured it falls back to a clearly-labelled deterministic mock generator so the workflow can
be exercised end to end. Mock output is always reported with ``is_mock=True`` and a note that
says so, so a mock draft is never presented as a real LLM result.

The reusable prompt templates live in this module as well: they are selected by industry and by
communication goal, and every template instructs the model to use only the prospect facts that
are supplied, so that a hallucinated company detail does not end up in a sales email.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

import httpx

from app.config import settings
from app.errors import UpstreamError
from app.services.lead_intelligence import INDUSTRY_REFERENCE

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

TONES = {
    "professional": (
        "Write in a professional, concise B2B register. No slang, no exclamation marks, "
        "no emoji, no filler praise."
    ),
    "friendly": (
        "Write in a friendly, warm but professional register. Direct, human, and never "
        "exaggerated or over-familiar."
    ),
}

LENGTHS = {
    "short": "Keep the whole email under 120 words.",
    "detailed": "Write 160-220 words with one concrete paragraph about the problem.",
}

GOALS = {
    "product_introduction": {
        "instruction": (
            "Introduce the product or service, state the problem it addresses for a company "
            "like this one, and close by inviting a short conversation."
        ),
        "call_to_action": "Suggest a brief introductory call.",
        "subject_hint": "a specific, benefit-oriented subject line",
    },
    "meeting": {
        "instruction": (
            "Ask for a short meeting. Reference one concrete operational problem that sales "
            "teams in this sector commonly face, without claiming to know anything about this "
            "company that was not supplied."
        ),
        "call_to_action": "Propose two concrete time slots for a 20-minute call.",
        "subject_hint": "a subject line that states the meeting request",
    },
    "follow_up": {
        "instruction": (
            "Write a short follow-up that adds one piece of value, references the earlier "
            "conversation generically, and asks whether the topic is still relevant."
        ),
        "call_to_action": "Ask for a simple yes or no reply.",
        "subject_hint": "a subject line that references the follow-up",
    },
}

BASE_SYSTEM_PROMPT = (
    "You are a B2B sales assistant. You write outbound sales emails for a sales team. "
    "Rules: use only the prospect facts provided; never invent company revenue, headcount, "
    "funding, customers, technologies or results; do not use placeholder text such as "
    "[Company] or [Name]; never use buzzwords or hype; keep the tone human. "
    "Return your answer as exactly two sections, in this order and with these exact headers:\n"
    "SUBJECT: <one subject line, no more than 80 characters>\n"
    "BODY: <the email body>"
)


@dataclass(frozen=True)
class PromptTemplate:
    """A fully resolved prompt template."""

    system_prompt: str
    user_prompt: str


def industry_guidance(industry: str | None) -> str:
    """Return sector-level guidance for the prompt, or a generic fallback."""
    if not industry:
        return (
            "Industry: not recorded. Use generic software-sales framing and avoid any "
            "assumption about the prospect's sector."
        )
    key = industry.strip().lower()
    payload = INDUSTRY_REFERENCE.get(key)
    if payload is None:
        for candidate, candidate_payload in INDUSTRY_REFERENCE.items():
            if candidate != "default" and (candidate in key or key in candidate):
                payload = candidate_payload
                key = candidate
                break
    if payload is None:
        payload = INDUSTRY_REFERENCE["default"]
        key = "general B2B"
    triggers = payload.get("triggers", [])
    guidance = (
        f"Industry: {industry}. Treat the following as sector-level context only - these are "
        "common patterns in this sector, not facts about this company: "
        + "; ".join(triggers)
        + "."
    )
    if key == "default":
        guidance = (
            f"Industry: {industry}. No sector reference is configured for this industry, so "
            "use general B2B framing and avoid sector-specific claims."
        )
    return guidance


def build_prompt(
    *,
    company_name: str,
    contact_name: str | None,
    industry: str | None,
    product_or_service: str,
    tone: str,
    email_length: str,
    communication_goal: str,
) -> PromptTemplate:
    """Build the system and user prompt for one outreach request."""
    goal = GOALS.get(communication_goal, GOALS["product_introduction"])
    tone_text = TONES.get(tone, TONES["professional"])
    length_text = LENGTHS.get(email_length, LENGTHS["short"])

    greeting_name = contact_name.strip() if contact_name and contact_name.strip() else None
    greeting = f"The contact is named {greeting_name}." if greeting_name else (
        "No contact name is recorded - greet them without a name."
    )

    user_prompt = f"""Write a sales email to the following prospect.

Prospect facts (use these only, do not add others):
- Company: {company_name}
- {greeting}
- Industry: {industry or "not recorded"}
- Offering: {product_or_service}

Objective: {goal['instruction']}
Call to action: {goal['call_to_action']}
Subject line: write {goal['subject_hint']}.
Tone: {tone_text}
Length: {length_text}

{industry_guidance(industry)}

Return the subject line and body using the exact SUBJECT: / BODY: headers."""
    return PromptTemplate(system_prompt=BASE_SYSTEM_PROMPT, user_prompt=user_prompt)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

SUBJECT_PATTERN = re.compile(r"^\s*subject\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
BODY_PATTERN = re.compile(r"^\s*body\s*:\s*(.*)$", re.IGNORECASE | re.MULTILINE | re.DOTALL)

MOCK_NOTE = (
    "Generated in mock mode: no LLM provider API key was configured, so this draft came "
    "from the offline template generator and was not produced by an AI model."
)


@dataclass
class GeneratedDraft:
    """The raw output of a generation run before it is persisted."""

    subject: str
    body: str
    provider: str
    is_mock: bool
    latency_ms: float
    notes: str | None = None


class OutreachGenerator:
    """Builds prompts, calls the configured provider and validates the response."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = timeout if timeout is not None else settings.llm_timeout_seconds
        self.max_retries = max_retries if max_retries is not None else settings.llm_max_retries
        self.transport = transport

    @property
    def is_configured(self) -> bool:
        """True when a provider API key is available."""
        return bool(self.api_key)

    # -- prompt ------------------------------------------------------------

    @staticmethod
    def build_prompt(
        *,
        company_name: str,
        contact_name: str | None,
        industry: str | None,
        product_or_service: str,
        tone: str,
        email_length: str,
        communication_goal: str,
    ) -> PromptTemplate:
        """Build the prompt for one generation request."""
        return build_prompt(
            company_name=company_name,
            contact_name=contact_name,
            industry=industry,
            product_or_service=product_or_service,
            tone=tone,
            email_length=email_length,
            communication_goal=communication_goal,
        )

    # -- provider ----------------------------------------------------------

    def _call_provider(self, prompt: PromptTemplate) -> str:
        """Call the chat-completions endpoint and return the raw completion text."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            "temperature": 0.4,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"

        last_error: Exception | None = None
        for _attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                    response = client.post(url, json=payload, headers=headers)
                if response.status_code >= 400:
                    raise UpstreamError(
                        f"LLM provider returned HTTP {response.status_code}",
                    )
                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    raise UpstreamError("LLM provider returned no choices")
                content = choices[0].get("message", {}).get("content")
                if not content or not str(content).strip():
                    raise UpstreamError("LLM provider returned an empty response")
                return str(content)
            except httpx.TimeoutException as exc:
                last_error = UpstreamError("LLM provider request timed out")
                last_error.__cause__ = exc
            except httpx.HTTPError as exc:
                last_error = UpstreamError("LLM provider request failed")
                last_error.__cause__ = exc
            except ValueError as exc:
                last_error = UpstreamError("LLM provider returned a malformed response")
                last_error.__cause__ = exc

        raise last_error or UpstreamError("LLM provider request failed")

    # -- response parsing --------------------------------------------------

    @staticmethod
    def parse_response(raw: str) -> tuple[str, str]:
        """Extract the subject and body from a provider response.

        Raises:
            UpstreamError: when the response does not contain a usable subject and body.
        """
        text = raw.strip()
        subject_match = SUBJECT_PATTERN.search(text)
        body_match = BODY_PATTERN.search(text)

        if subject_match is None or body_match is None:
            raise UpstreamError(
                "LLM response did not contain the expected SUBJECT: and BODY: sections"
            )

        subject = subject_match.group(1).strip().strip('"').strip()
        body = body_match.group(1).strip()
        body = re.sub(r"\n{3,}", "\n\n", body)

        if not subject or not body:
            raise UpstreamError("LLM response contained an empty subject or body")
        return subject, body

    # -- mock ---------------------------------------------------------------

    @staticmethod
    def build_mock_draft(
        *,
        company_name: str,
        contact_name: str | None,
        industry: str | None,
        product_or_service: str,
        tone: str,
        email_length: str,
        communication_goal: str,
    ) -> GeneratedDraft:
        """Build a deterministic offline draft used when no provider is configured."""
        greeting_name = contact_name.strip() if contact_name and contact_name.strip() else "there"
        industry_text = f" in {industry}" if industry else ""
        subject_templates = {
            "product_introduction": f"{product_or_service} for {company_name}",
            "meeting": f"20 minutes to review lead operations at {company_name}",
            "follow_up": f"Following up - {product_or_service}",
        }
        subject = subject_templates.get(
            communication_goal, subject_templates["product_introduction"]
        )

        opening = f"Hi {greeting_name}," if contact_name else "Hello,"
        if tone == "friendly":
            opening += " hope you are well."

        body_lines = [
            opening,
            "",
            f"I work with sales teams{industry_text} that spend a lot of time on prospect data "
            f"entry, company research and first-touch email preparation.",
            "",
            f"{product_or_service} is built for that workflow: one prospect database with "
            "validation and duplicate detection, company insights generated from the record "
            "itself, a transparent qualification score, and outreach drafts that a rep reviews "
            "before sending.",
        ]

        if communication_goal == "meeting":
            body_lines += [
                "",
                "Would a 20-minute call next week work to map it against how your team "
                "handles leads today? I can send two slot options that suit you.",
            ]
        elif communication_goal == "follow_up":
            body_lines += [
                "",
                "Is this still relevant for your team, or should I close the loop? A one-line "
                "reply either way is fine.",
            ]
        else:
            body_lines += [
                "",
                "If it would help, I can share a short walkthrough of how it handles a "
                "prospect list end to end.",
            ]

        body_lines += ["", "Best regards,", "Sales Team"]

        body = "\n".join(body_lines)
        if email_length == "detailed":
            body += (
                "\n\nA typical rollout starts with importing the existing prospect list, "
                "reviewing the validation and duplicate report, and then switching the team "
                "onto scored records rather than raw spreadsheet rows."
            )

        return GeneratedDraft(
            subject=subject,
            body=body,
            provider="mock",
            is_mock=True,
            latency_ms=0.0,
            notes=MOCK_NOTE,
        )

    # -- public API --------------------------------------------------------

    def generate(
        self,
        *,
        company_name: str,
        contact_name: str | None,
        industry: str | None,
        product_or_service: str,
        tone: str = "professional",
        email_length: str = "short",
        communication_goal: str = "product_introduction",
    ) -> GeneratedDraft:
        """Generate an outreach draft, using the provider when one is configured."""
        if not self.is_configured:
            return self.build_mock_draft(
                company_name=company_name,
                contact_name=contact_name,
                industry=industry,
                product_or_service=product_or_service,
                tone=tone,
                email_length=email_length,
                communication_goal=communication_goal,
            )

        prompt = self.build_prompt(
            company_name=company_name,
            contact_name=contact_name,
            industry=industry,
            product_or_service=product_or_service,
            tone=tone,
            email_length=email_length,
            communication_goal=communication_goal,
        )

        started = time.perf_counter()
        raw = self._call_provider(prompt)
        latency_ms = (time.perf_counter() - started) * 1000
        subject, body = self.parse_response(raw)
        return GeneratedDraft(
            subject=subject,
            body=body,
            provider=self.model,
            is_mock=False,
            latency_ms=round(latency_ms, 2),
            notes=None,
        )


__all__ = [
    "BASE_SYSTEM_PROMPT",
    "GOALS",
    "LENGTHS",
    "MOCK_NOTE",
    "TONES",
    "GeneratedDraft",
    "OutreachGenerator",
    "PromptTemplate",
    "build_prompt",
    "industry_guidance",
]
