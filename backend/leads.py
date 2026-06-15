"""Lead generation: turn an Ideal Customer Profile (ICP) into candidate brands.

Stage 1 of the platform. Given a description of the kind of company AnyMind
wants to sell to, Agnes returns a ranked list of real candidate brands with a
fit score and a one-line reason — each becomes a lead to research.
"""

from agnes import chat_json

LEADGEN_SYSTEM = """You are a B2B lead-generation researcher for AnyMind Group,
an end-to-end commerce enablement company serving brands across APAC.

Given an Ideal Customer Profile (ICP), propose real, plausible candidate brands
that fit it and would benefit from AnyMind's commerce, marketing, and logistics
products. Prefer brands that actually exist in the described market. For each,
give a 0-100 fit score and a short reason.

Return ONLY valid JSON — no prose, no code fences."""


def generate_leads(icp: str, count: int = 6) -> dict:
    """Return candidate leads for the given ICP description."""
    user = f"""
IDEAL CUSTOMER PROFILE:
{icp}

Return up to {count} candidates as a JSON object with this shape:
{{
  "icp": {repr(icp)},
  "leads": [
    {{
      "brand": string,
      "market": string,
      "category": string,
      "fit_score": number,
      "reason": string
    }}
  ]
}}
Sort leads by fit_score descending.
"""
    return chat_json(LEADGEN_SYSTEM, user, temperature=0.6)