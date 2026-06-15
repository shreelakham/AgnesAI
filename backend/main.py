"""FastAPI backend for AnyPitch — AnyMind Sales Intelligence.

Pipeline endpoints:
  POST /api/leads              ICP            -> candidate brands (Agnes text)
  POST /api/research           brand          -> competitive analysis (Agnes text)
  POST /api/image              pitch [+asset] -> concept image (Agnes image / img2img)
  POST /api/video              pitch [+asset] -> concept video (Agnes video)
  POST /api/deck               pitch [+image] -> downloadable .pptx
  POST /api/forecast           pitch          -> customer revenue forecast
  POST /api/roleplay           pitch+history  -> buyer reply (Agnes text, roleplay)
  POST /api/roleplay/feedback  pitch+history  -> coaching (Agnes text)

Run:  uvicorn main:app --reload --port 8000   (then open http://localhost:8000)
"""

import os
import uuid

from fastapi import FastAPI, Body, HTTPException
from fastapi.staticfiles import StaticFiles

from leads import generate_leads
from pitch import (build_pitch, generate_concept_image, generate_concept_video,
                   generate_market_image, generate_market_headline, MARKET_STYLES)
from deck import build_deck
from revenue import build_dashboard
from roleplay import buyer_reply, coach_feedback, suggest_pitch

BASE = os.path.dirname(os.path.abspath(__file__))
GEN_DIR = os.path.join(BASE, "generated")
FRONTEND = os.path.join(os.path.dirname(BASE), "frontend")
os.makedirs(GEN_DIR, exist_ok=True)

app = FastAPI(title="AnyPitch")


def _need_pitch(payload: dict) -> dict:
    pitch = payload.get("pitch") or {}
    if not pitch.get("brand"):
        raise HTTPException(400, "Provide a 'pitch' object.")
    return pitch


@app.post("/api/leads")
def api_leads(payload: dict = Body(...)):
    icp = (payload.get("icp") or "").strip()
    if not icp:
        raise HTTPException(400, "Provide an 'icp' description.")
    return generate_leads(icp, int(payload.get("count", 6)))


@app.post("/api/research")
def api_research(payload: dict = Body(...)):
    brand = (payload.get("brand") or "").strip()
    if not brand:
        raise HTTPException(400, "Provide a 'brand'.")
    return build_pitch(brand, payload.get("context"))


@app.post("/api/image")
def api_image(payload: dict = Body(...)):
    pitch = _need_pitch(payload)
    init = payload.get("init_image")          # optional Data URI / URL (img2img)
    try:
        png, remote_url = generate_concept_image(pitch, init_image=init)
    except Exception as e:
        raise HTTPException(502, f"Image generation failed: {e}")
    name = f"img_{uuid.uuid4().hex[:10]}.png"
    with open(os.path.join(GEN_DIR, name), "wb") as f:
        f.write(png)
    # image_remote_url is Agnes' public URL -> feed it into image-to-video.
    return {"image_url": f"/generated/{name}", "image_file": name,
            "image_remote_url": remote_url}


@app.post("/api/video")
def api_video(payload: dict = Body(...)):
    pitch = _need_pitch(payload)
    init = payload.get("init_image")
    try:
        mp4 = generate_concept_video(pitch, init_image=init)
    except Exception as e:
        raise HTTPException(502, f"Video generation failed: {e}")
    name = f"vid_{uuid.uuid4().hex[:10]}.mp4"
    with open(os.path.join(GEN_DIR, name), "wb") as f:
        f.write(mp4)
    return {"video_url": f"/generated/{name}", "video_file": name}


@app.get("/api/markets")
def api_markets_list():
    return {"markets": list(MARKET_STYLES.keys())}


@app.post("/api/market")
def api_market(payload: dict = Body(...)):
    pitch = _need_pitch(payload)
    market = (payload.get("market") or "").strip()
    init = payload.get("init_image")
    if not market:
        raise HTTPException(400, "Provide a 'market'.")
    if not init:
        raise HTTPException(400, "Provide 'init_image' (product photo).")
    try:
        png, remote = generate_market_image(pitch, market, init)
    except Exception as e:
        raise HTTPException(502, f"Market creative failed: {e}")
    headline, gloss = "", ""
    try:
        h = generate_market_headline(pitch, market)
        headline, gloss = h.get("headline", ""), h.get("english_gloss", "")
    except Exception:
        pass  # tile still works without copy
    name = f"mkt_{uuid.uuid4().hex[:10]}.png"
    with open(os.path.join(GEN_DIR, name), "wb") as f:
        f.write(png)
    return {"market": market, "image_url": f"/generated/{name}",
            "image_remote_url": remote, "headline": headline,
            "english_gloss": gloss}


@app.post("/api/deck")
def api_deck(payload: dict = Body(...)):
    pitch = _need_pitch(payload)
    image_bytes = None
    img_file = payload.get("image_file")
    if img_file:
        path = os.path.join(GEN_DIR, os.path.basename(img_file))
        if os.path.exists(path):
            with open(path, "rb") as f:
                image_bytes = f.read()
    pptx = build_deck(pitch, image_bytes)
    name = f"deck_{uuid.uuid4().hex[:10]}.pptx"
    with open(os.path.join(GEN_DIR, name), "wb") as f:
        f.write(pptx)
    return {"deck_url": f"/generated/{name}", "deck_file": name}


@app.post("/api/forecast")
def api_forecast(payload: dict = Body(...)):
    pitch = _need_pitch(payload)
    a = payload.get("assumptions") or {}
    return build_dashboard(
        pitch,
        start_revenue=float(a.get("start_revenue", 800_000)),
        organic_growth=float(a.get("organic_growth", 0.02)),
        months=int(a.get("months", 18)),
    )


@app.post("/api/roleplay")
def api_roleplay(payload: dict = Body(...)):
    pitch = _need_pitch(payload)
    msg = (payload.get("message") or "").strip()
    if not msg:
        raise HTTPException(400, "Provide a 'message'.")
    return {"reply": buyer_reply(pitch, payload.get("history") or [], msg)}


@app.post("/api/roleplay/feedback")
def api_roleplay_feedback(payload: dict = Body(...)):
    pitch = _need_pitch(payload)
    return coach_feedback(pitch, payload.get("history") or [])


@app.post("/api/roleplay/suggest")
def api_roleplay_suggest(payload: dict = Body(...)):
    pitch = _need_pitch(payload)
    return suggest_pitch(pitch, payload.get("history") or [])


# Generated artifacts (images, videos, decks) and the static frontend.
app.mount("/generated", StaticFiles(directory=GEN_DIR), name="generated")
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")