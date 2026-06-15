"""Pitch generation: turn a brand into a competitive analysis + pitch package."""

import json

from products import catalogue_text
from agnes import chat_json, generate_image


SYSTEM_PROMPT = """You are a senior sales-enablement strategist at AnyMind Group,
an end-to-end commerce enablement company. Given a brand, you build a complete,
pitch-ready package.

Method, in order:
1. Summarise the brand and its competitive position.
2. Identify the brand's key gaps / unmet needs.
3. Map AnyMind products (ONLY from the supplied catalogue) onto each gap.
4. Bundle the best-fit products into ONE recommended package.
5. Project the upside (revenue/profit uplift + time/efficiency saved).

Keep it pitch-ready: confident, concise, persuasive. This is a sales pitch,
not a due-diligence report. Express the upside as a clean low-to-high range
with a short one-line basis, and anchor to any real brand metrics you were given.

Return ONLY valid JSON — no prose, no markdown code fences."""


def _build_prompt(brand: str, brand_context: dict | None) -> str:
    context_block = (
        json.dumps(brand_context, ensure_ascii=False, indent=2)
        if brand_context else "None provided — estimates will be illustrative."
    )
    return f"""
BRAND TO ANALYSE: {brand}

KNOWN BRAND FACTS (use these to anchor any numbers):
{context_block}

ANYMIND PRODUCT CATALOGUE (only recommend from this list):
{catalogue_text()}

Build the pitch. Return a JSON object with EXACTLY this shape:
{{
  "brand": "{brand}",
  "brand_summary": string,
  "competitive_position": string,
  "likely_competitors": [string],
  "gaps": [
    {{"gap": string, "why_it_matters": string, "severity": "high | medium | low"}}
  ],
  "solution_mapping": [
    {{"product": string, "gap_addressed": string, "how_it_helps": string}}
  ],
  "recommended_package": {{
    "package_name": string,
    "included_products": [string],
    "rationale": string,
    "suggested_engagement": string
  }},
  "projected_impact": {{
    "revenue_or_profit_uplift": {{"low": string, "high": string, "timeframe": string, "basis": string}},
    "time_or_efficiency_gain": {{"low": string, "high": string, "what_it_speeds_up": string}},
    "time_to_value": string
  }},
  "headline_pitch": string
}}
"""


def build_pitch(brand: str, brand_context: dict | None = None) -> dict:
    """Run a full competitive analysis + pitch package for `brand`."""
    return chat_json(SYSTEM_PROMPT, _build_prompt(brand, brand_context))


def build_image_prompt(pitch: dict) -> str:
    """Derive a concept-visualisation prompt from the pitch.

    Follows Agnes' recommended structure:
    [Subject] + [Scene] + [Style] + [Lighting] + [Composition] + [Quality].
    """
    brand = pitch.get("brand", "the brand")
    pkg = pitch.get("recommended_package", {})
    package_name = pkg.get("package_name", "growth solution package")
    products = ", ".join(pkg.get("included_products", [])) or "AnyMind products"
    return (
        f"A sleek isometric business concept illustration representing the brand "
        f"'{brand}' accelerating growth through a unified commerce platform "
        f"(the '{package_name}', powering {products}); "
        f"scene of connected dashboards, product and influencer icons flowing "
        f"into a central hub with upward-trending growth arrows; "
        f"modern corporate infographic style, deep teal and navy palette with "
        f"mint accents; soft clean studio lighting; balanced wide composition "
        f"with a clear focal hub; high detail, high visual density, minimal "
        f"text, professional and optimistic."
    )


def generate_concept_image(pitch: dict) -> bytes:
    """Build the prompt from the pitch and return PNG bytes."""
    return generate_image(build_image_prompt(pitch))