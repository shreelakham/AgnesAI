"""FastAPI backend for the Agnes Pitch Builder.

Pipeline endpoints:
  POST /api/leads      ICP            -> candidate brands (Agnes text)
  POST /api/research   brand          -> competitive analysis + pitch (Agnes text)
  POST /api/image      pitch          -> concept image (Agnes image)
  POST /api/deck       pitch [+image] -> downloadable .pptx
  POST /api/dashboard  pitch          -> AnyMind revenue projections

Run:  uvicorn main:app --reload --port 8000   (then open http://localhost:8000)
"""

import os
import uuid

from fastapi import FastAPI, Body, HTTPException
from fastapi.staticfiles import StaticFiles

from leads import generate_leads
from pitch import build_pitch, generate_concept_image
from deck import build_deck
from revenue import build_dashboard

BASE = os.path.dirname(os.path.abspath(__file__))
GEN_DIR = os.path.join(BASE, "generated")
FRONTEND = os.path.join(os.path.dirname(BASE), "frontend")
os.makedirs(GEN_DIR, exist_ok=True)

app = FastAPI(title="Agnes Pitch Builder")


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
    pitch = payload.get("pitch") or {}
    if not pitch.get("brand"):
        raise HTTPException(400, "Provide a 'pitch' object.")
    try:
        png = generate_concept_image(pitch)
    except Exception as e:
        raise HTTPException(502, f"Image generation failed: {e}")
    name = f"img_{uuid.uuid4().hex[:10]}.png"
    with open(os.path.join(GEN_DIR, name), "wb") as f:
        f.write(png)
    return {"image_url": f"/generated/{name}", "image_file": name}


@app.post("/api/deck")
def api_deck(payload: dict = Body(...)):
    pitch = payload.get("pitch") or {}
    if not pitch.get("brand"):
        raise HTTPException(400, "Provide a 'pitch' object.")
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


@app.post("/api/dashboard")
def api_dashboard(payload: dict = Body(...)):
    pitch = payload.get("pitch") or {}
    if not pitch.get("brand"):
        raise HTTPException(400, "Provide a 'pitch' object.")
    a = payload.get("assumptions") or {}
    return build_dashboard(
        pitch,
        start_gmv=float(a.get("start_gmv", 500_000)),
        monthly_growth=float(a.get("monthly_growth", 0.04)),
        months=int(a.get("months", 18)),
    )


# Generated artifacts (images, decks) and the static frontend.
app.mount("/generated", StaticFiles(directory=GEN_DIR), name="generated")
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")