# AnyPitch — AnyMind Sales Intelligence

**From "who should we sell to" to a rehearsed, localized, ready-to-send pitch — powered by Agnes AI.**

AnyPitch is an end-to-end sales-enablement tool for AnyMind Group's Business Development team. Given a description of the kind of company AnyMind wants to win, it finds candidate brands, builds a full competitive analysis and product-fit pitch, lets the rep rehearse it against an AI buyer, turns the brand's own product photo into marketing-grade creative (image, video and localized variants for different markets) and forecasts the revenue upside the brand itself would unlock — then exports everything as a ready .pptx deck.

## How it works

The app is a five-stage pipeline, each stage building on the last:

1. **Leads** — describe an Ideal Customer Profile (ICP); Agnes finds and scores real candidate brands that fit it.
2. **Research** — pick a brand and Agnes builds a full pitch package: a summary of the brand and its competitive position, the gaps in their current setup, which AnyMind products close each gap, a recommended bundle and the projected upside — all as structured JSON that drives every later stage.
3. **Practice** — rehearse the pitch live against an AI buyer playing that brand's CMO. The buyer stays in character, raises real objections and a coaching layer scores the conversation and can suggest the rep's next line.
4. **Studio** — upload the brand's actual product photo. Agnes enhances it into premium marketing creative (image-to-image), animates that enhanced image into a short 9:16 product video (image-to-video) and generates localized creative variants — re-styled visuals plus a native-language headline — for different consumer markets (Japan, South Korea, Indonesia, the Middle East, the US, Brazil). The full pitch deck (.pptx) exports from here, using the enhanced image if one's been generated.
5. **Forecast** — a transparent, deterministic model projects the *brand's own* revenue under a do-nothing baseline versus three adoption strategies — Quick Win, Full Transformation and Phased Rollout — so the pitch shows the prospect their own upside.

## Built with Agnes AI

AnyPitch is built across all three Agnes modalities — text, image and video — combined in ways that go beyond a single API call per feature:

| Stage | Agnes capability | What it does |
|---|---|---|
| Leads | Text (`agnes-2.0-flash`) | Finds and scores real candidate brands against an ICP |
| Research | Text (`agnes-2.0-flash`) | Structured gap analysis, product mapping, and revenue projection as JSON — the backbone every other stage reads from |
| Practice | Text (`agnes-2.0-flash`) | A live, in-character AI buyer persona that responds to the pitch and raises objections |
| Practice | Text (`agnes-2.0-flash`) | Coaching: scores the conversation, surfaces missed objections and can suggest the rep's next line |
| Studio — Enhance | Image (`agnes-image-2.1-flash`, image-to-image) | Turns an uploaded product photo into premium marketing creative while preserving the real product |
| Studio — Video | Video (`agnes-video-v2.0`, image-to-video) | Animates the enhanced image into a short, polished 9:16 product video |
| Studio — Localize | Image (image-to-image) **+** Text | Re-styles the enhanced image per target market *and* writes a native-language headline for that market — a text + image combination per locale |

The revenue forecast deliberately uses a deterministic formula rather than another LLM call — the numbers shown to a prospect need to be defensible and reproducible, not generated.

## Tech stack

- **Backend**: FastAPI (Python), serving both the API and the static frontend
- **Frontend**: vanilla HTML/CSS/JS + Chart.js (no build step, no npm)
- **Deck export**: `python-pptx` — generates a real, editable `.pptx`
- **Agnes AI**: OpenAI-compatible text endpoint (`agnes-2.0-flash`) via the `openai` SDK; image (`agnes-image-2.1-flash`) and video (`agnes-video-v2.0`) via direct HTTP (`httpx`), since their request shapes fall outside the SDK's standard image/video methods

## Project structure

```
AgnesAI/
├── .env                  # Agnes API credentials & model config (not committed)
├── backend/
│   ├── main.py           # FastAPI app — all API endpoints
│   ├── agnes.py          # Agnes API client (text, image, video)
│   ├── pitch.py           # Pitch generation, image/video/market prompts
│   ├── roleplay.py         # AI buyer persona + coaching
│   ├── revenue.py          # Deterministic revenue forecast model
│   ├── products.py          # AnyMind product catalogue + impact assumptions
│   ├── deck.py               # .pptx deck builder
│   ├── requirements.txt
│   └── generated/             # Output images, videos, decks (served at /generated)
└── frontend/
    ├── index.html
    ├── app.js
    └── styles.css
```

## Setup & running

1. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure `.env`** (project root) with your Agnes API credentials:
   ```
   API_KEY=sk-...
   BASE_URL=https://apihub.agnes-ai.com/v1
   TEXT_MODEL=agnes-2.0-flash
   IMAGE_ENDPOINT=https://apihub.agnes-ai.com/v1/images/generations
   IMAGE_MODEL=agnes-image-2.1-flash
   ```
   > `BASE_URL` must be the API root (no trailing `/chat/completions`) — the OpenAI SDK appends that itself.

3. **Run**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   Open **http://localhost:8000** — the backend serves the frontend directly, no separate dev server needed.

## Notes

- All product recommendations are constrained to AnyMind's real product catalogue (`products.py`) — Agnes can't recommend something AnyMind doesn't sell.
- Image-to-video requires a publicly reachable image URL; the enhance step returns Agnes's hosted URL for this purpose, so video generation is only available after enhancing.
- Video generation is asynchronous and can take 1–2 minutes (create-task → poll → download).