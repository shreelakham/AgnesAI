"""Buyer roleplay simulator.

Agnes plays the prospect's decision-maker so a rep can rehearse the pitch.
Two modes:
  buyer_reply()    - the buyer responds in character to the rep's message.
  coach_feedback() - scores how the rep did and gives concrete coaching.
"""

import json

from agnes import chat_text, chat_json


def _persona(pitch: dict) -> str:
    brand = pitch.get("brand", "the brand")
    gaps = "; ".join(g.get("gap", "") for g in pitch.get("gaps", [])[:3])
    return f"""You are the Chief Marketing Officer of {brand}. A salesperson from
AnyMind Group is pitching you. Stay fully in character as a busy, sharp, slightly
skeptical buyer. You care about ROI, switching cost, and proof.

Context AnyMind believes about you (use it, but don't recite it):
- Known gaps/pain points: {gaps or "operational and marketing inefficiencies"}.

Behave realistically:
- Open guarded; warm up only if the rep gives specific, credible answers.
- Raise concrete objections (price, integration effort, proof, timing).
- Ask pointed follow-ups. Don't volunteer to buy easily.
- Keep replies to 2-4 sentences, conversational, first person.
Never break character or mention you are an AI."""


def buyer_reply(pitch: dict, history: list, message: str) -> str:
    """Return the buyer's in-character reply to the rep's latest message."""
    messages = [{"role": "system", "content": _persona(pitch)}]
    # history is a list of {"role": "rep"|"buyer", "content": str}
    for turn in history:
        role = "user" if turn.get("role") == "rep" else "assistant"
        messages.append({"role": role, "content": turn.get("content", "")})
    messages.append({"role": "user", "content": message})
    return chat_text(messages, temperature=0.8)


COACH_SYSTEM = """You are a sales coach reviewing a roleplay between an AnyMind
rep (the "rep") and a prospect (the "buyer"). Give honest, specific, useful
feedback. Return ONLY valid JSON — no prose, no code fences."""


SUGGEST_SYSTEM = """You are a real-time sales coach for an AnyMind rep mid-pitch.
Using the pitch facts and the conversation so far, suggest the single best thing
the rep should say next. Be concrete and persuasive; use the gaps, package and
projected impact as ammunition. Return ONLY valid JSON — no prose, no code fences."""


def _pitch_brief(pitch: dict) -> str:
    pkg = pitch.get("recommended_package", {})
    gaps = "; ".join(g.get("gap", "") for g in pitch.get("gaps", [])[:3])
    imp = pitch.get("projected_impact", {}).get("revenue_or_profit_uplift", {})
    return (f'Brand: {pitch.get("brand")}. '
            f'Package: {pkg.get("package_name")} ({", ".join(pkg.get("included_products", []))}). '
            f'Top gaps: {gaps}. '
            f'Impact: {imp.get("low","")}–{imp.get("high","")} uplift. '
            f'Headline: {pitch.get("headline_pitch","")}')


def suggest_pitch(pitch: dict, history: list) -> dict:
    """Suggest what the rep should say next (or how to open)."""
    transcript = "\n".join(
        f'{"REP" if t.get("role") == "rep" else "BUYER"}: {t.get("content","")}'
        for t in history
    ) or "(no conversation yet — suggest a strong opening line)"
    user = f"""
PITCH FACTS: {_pitch_brief(pitch)}

CONVERSATION SO FAR:
{transcript}

Return JSON with this shape:
{{
  "suggested_line": string,        // the exact words the rep could say next
  "talking_points": [string],      // 2-3 supporting points to weave in
  "why": string                    // one line on why this works now
}}
"""
    return chat_json(SUGGEST_SYSTEM, user, temperature=0.5)


def coach_feedback(pitch: dict, history: list) -> dict:
    """Score the rep's performance and give coaching."""
    transcript = "\n".join(
        f'{"REP" if t.get("role") == "rep" else "BUYER"}: {t.get("content","")}'
        for t in history
    )
    user = f"""
BRAND BEING PITCHED: {pitch.get("brand")}

TRANSCRIPT:
{transcript}

Return JSON with this shape:
{{
  "score": number,                      // 0-100 overall
  "what_worked": [string],
  "what_to_improve": [string],
  "missed_objections": [string],
  "one_thing_to_try_next": string
}}
"""
    return chat_json(COACH_SYSTEM, user, temperature=0.4)