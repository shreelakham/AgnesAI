"""Pitch generation: turn a brand into a competitive analysis + pitch package."""

import json

from products import catalogue_text
from agnes import chat_json, generate_image, generate_video


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
    """Prompt to ENHANCE an uploaded product photo into premium marketing creative.
    Used with image-to-image, so it preserves the product while elevating it."""
    brand = pitch.get("brand", "the brand")
    return (
        f"Enhance this product photo into a premium marketing visual for '{brand}'. "
        f"Keep the product's exact identity, shape, label and colours, but elevate "
        f"everything around it: clean professional studio lighting, crisp sharp focus, "
        f"refined complementary background, subtle reflections and soft shadows, "
        f"vibrant true-to-life colours, advertising-grade product photography with "
        f"room for a short headline. Scroll-stopping e-commerce hero image."
    )


def generate_concept_image(pitch: dict, init_image: str | None = None):
    """Return (png_bytes, public_url). Pass the uploaded product image as
    init_image (URL or Data URI) for image-to-image enhancement."""
    prompt = build_image_prompt(pitch)
    if init_image:
        prompt = "Using the supplied product image as the subject. " + prompt
    return generate_image(prompt, init_image=init_image)


def build_video_prompt(pitch: dict) -> str:
    """Prompt for an informative, engaging short product video (image-to-video)."""
    brand = pitch.get("brand", "the brand")
    return (
        f"An engaging, informative short product video for '{brand}', built from "
        f"the supplied image. Smoothly reveal the product with gentle cinematic "
        f"motion — a slow push-in, subtle rotation and light parallax — to highlight "
        f"its form, texture and key details. Clean premium studio setting, soft "
        f"dynamic lighting, polished e-commerce feel. Keep the product's identity, "
        f"packaging and colours perfectly consistent throughout."
    )


def generate_concept_video(pitch: dict, init_image: str | None = None) -> bytes:
    """Return MP4 bytes of a vertical product video (9:16). init_image should be
    a PUBLIC image URL (e.g. the enhanced image's URL)."""
    return generate_video(build_video_prompt(pitch), init_image=init_image,
                          width=768, height=1152)