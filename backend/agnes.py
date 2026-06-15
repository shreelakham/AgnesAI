"""Agnes AI client wrappers.

Two capabilities:
  - chat_json(): call the Agnes text model and parse a JSON reply.
  - generate_image(): call the Agnes image model (direct HTTP, because the
    image API expects response_format nested inside an `extra_body` object,
    a shape the OpenAI SDK can't produce cleanly).

Environment variables (see .env.example):
  API_KEY        - Agnes API key (Bearer token)
  BASE_URL       - Agnes chat endpoint, e.g. https://apihub.agnes-ai.com/v1
  IMAGE_ENDPOINT - optional override for the image endpoint
"""

import os
import json
import base64

import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---- Text model (OpenAI-compatible) ---------------------------------------
client = OpenAI(
    api_key=os.environ["API_KEY"],
    base_url=os.environ["BASE_URL"],
    timeout=90,
)
TEXT_MODEL = os.environ.get("TEXT_MODEL", "agnes-2.0-flash")

# ---- Image model (direct HTTP per Agnes docs) -----------------------------
IMAGE_ENDPOINT = os.environ.get(
    "IMAGE_ENDPOINT", "https://apihub.agnes-ai.com/v1/images/generations"
)
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "agnes-image-2.1-flash")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x768")


def chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> dict:
    """Call the text model and return parsed JSON (resilient to code fences)."""
    resp = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=3000,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        brace = raw.find("{")
        if brace != -1:
            raw = raw[brace:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_parse_error": True, "raw_output": raw}


def generate_image(prompt: str) -> bytes:
    """Call the Agnes image model and return raw PNG bytes."""
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": IMAGE_SIZE,
        # Per Agnes docs: response_format must live INSIDE extra_body.
        "extra_body": {"response_format": "url"},
    }
    headers = {
        "Authorization": f"Bearer {os.environ['API_KEY']}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(IMAGE_ENDPOINT, json=payload, headers=headers, timeout=360)
    resp.raise_for_status()
    data = resp.json()["data"][0]

    if data.get("url"):
        return httpx.get(data["url"], timeout=360).content
    if data.get("b64_json"):
        return base64.b64decode(data["b64_json"])
    raise RuntimeError(f"Unexpected image response: {data!r}")