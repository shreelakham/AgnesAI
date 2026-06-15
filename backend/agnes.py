"""Agnes AI client wrappers.

  - chat_json()      : text model -> parsed JSON reply
  - chat_text()      : text model -> free-form reply (roleplay)
  - generate_image() : image model -> (png_bytes, public_url)
  - generate_video() : async video task (create -> poll -> download)

generate_image returns the PUBLIC url Agnes hosts the result at, so an enhanced
image can be fed straight into image-to-video (which needs a reachable URL).
"""

import os
import json
import time
import base64

import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---- Text model (OpenAI-compatible) ---------------------------------------
client = OpenAI(api_key=os.environ["API_KEY"], base_url=os.environ["BASE_URL"], timeout=90)
TEXT_MODEL = os.environ.get("TEXT_MODEL", "agnes-2.0-flash")

# ---- Image model ----------------------------------------------------------
IMAGE_ENDPOINT = os.environ.get("IMAGE_ENDPOINT", "https://apihub.agnes-ai.com/v1/images/generations")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "agnes-image-2.1-flash")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x1024")

# ---- Video model (async task API) -----------------------------------------
VIDEO_CREATE = os.environ.get("VIDEO_CREATE", "https://apihub.agnes-ai.com/v1/videos")
VIDEO_POLL = os.environ.get("VIDEO_POLL", "https://apihub.agnes-ai.com/agnesapi")
VIDEO_MODEL = os.environ.get("VIDEO_MODEL", "agnes-video-v2.0")
VIDEO_W = int(os.environ.get("VIDEO_W", "1152"))
VIDEO_H = int(os.environ.get("VIDEO_H", "768"))
VIDEO_FRAMES = int(os.environ.get("VIDEO_FRAMES", "121"))   # ~5s @24fps, 8n+1
VIDEO_FPS = int(os.environ.get("VIDEO_FPS", "24"))


def chat_json(system_prompt, user_prompt, temperature=0.4):
    resp = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt}],
        temperature=temperature, max_tokens=3000)
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        b = raw.find("{")
        if b != -1:
            raw = raw[b:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_parse_error": True, "raw_output": raw}


def chat_text(messages, temperature=0.7):
    resp = client.chat.completions.create(
        model=TEXT_MODEL, messages=messages, temperature=temperature, max_tokens=900)
    return resp.choices[0].message.content.strip()


def _headers():
    return {"Authorization": f"Bearer {os.environ['API_KEY']}", "Content-Type": "application/json"}


def generate_image(prompt, init_image=None):
    """Text-to-image, or image-to-image when init_image (URL or Data URI) given.
    Returns (png_bytes, public_url). public_url is None if the API returns base64."""
    extra = {"response_format": "url"}
    if init_image:
        extra["image"] = [init_image]
    payload = {"model": IMAGE_MODEL, "prompt": prompt, "size": IMAGE_SIZE, "extra_body": extra}
    resp = httpx.post(IMAGE_ENDPOINT, json=payload, headers=_headers(), timeout=360)
    resp.raise_for_status()
    data = resp.json()["data"][0]
    if data.get("url"):
        url = data["url"]
        return httpx.get(url, timeout=360).content, url
    if data.get("b64_json"):
        return base64.b64decode(data["b64_json"]), None
    raise RuntimeError(f"Unexpected image response: {data!r}")


def _extract_video_url(body):
    data = body.get("data")
    if isinstance(data, list) and data:
        return data[0].get("url") or data[0].get("video_url")
    return body.get("url") or body.get("video_url")


def generate_video(prompt, init_image=None, width=None, height=None):
    """Async video. POST /v1/videos -> poll /agnesapi?video_id -> download.
    init_image must be a PUBLIC URL for image-to-video."""
    payload = {"model": VIDEO_MODEL, "prompt": prompt,
               "width": width or VIDEO_W, "height": height or VIDEO_H,
               "num_frames": VIDEO_FRAMES, "frame_rate": VIDEO_FPS}
    if init_image and str(init_image).startswith("http"):
        payload["image"] = init_image
    created = httpx.post(VIDEO_CREATE, json=payload, headers=_headers(), timeout=120)
    created.raise_for_status()
    task = created.json()
    video_id = task.get("video_id") or task.get("id")
    if not video_id:
        raise RuntimeError(f"No video_id in create response: {task!r}")
    for _ in range(72):
        time.sleep(5)
        poll = httpx.get(VIDEO_POLL, params={"video_id": video_id},
                         headers=_headers(), timeout=60).json()
        status = poll.get("status")
        if status == "completed":
            url = poll.get("remixed_from_video_id") or _extract_video_url(poll)
            if not url:
                raise RuntimeError(f"Completed but no URL: {poll!r}")
            return httpx.get(url, timeout=600).content
        if status == "failed":
            raise RuntimeError(f"Video task failed: {poll.get('error')}")
    raise RuntimeError("Video task timed out.")