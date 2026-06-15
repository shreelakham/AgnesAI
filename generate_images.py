"""
generate_images.py
-------------------
Reads deck/assets/analysis.json, builds an abstract/conceptual image prompt
for each "gap" and each "solution", calls Agnes AI's image generation
endpoint, saves the results into deck/assets/, and writes the resulting
file paths back into analysis.json (as the "image" field the deck already
knows how to render).

Setup
-----
1. pip install requests --break-system-packages
2. Set your Agnes API key as an environment variable before running:
       export AGNES_API_KEY="sk-..."          (macOS / Linux)
       set AGNES_API_KEY=sk-...               (Windows cmd)
3. Run from the project root:
       python generate_images.py
   Add --dry-run to print the prompts without calling the API or
   spending credits — useful for sanity-checking wording first.

What it does NOT do
--------------------
- Does not touch "competitors"/"axes" (this deck uses the gap-analysis
  schema, not the perceptual-map schema).
- Does not generate the marketing video — that's a separate script
  against /v1/video/generations (async job + polling).
- Does not invent a theme — if analysis.json has no "theme" block, a
  neutral default palette is used for the prompt's style suffix.
"""

import base64
import json
import os
import sys
import time
import urllib.request

# ---------------------------------------------------------------- config --

API_BASE = "https://apihub.agnes-ai.com/v1"
IMAGE_MODEL = "agnes-image-2.1-flash"

ANALYSIS_PATH = os.path.join("assets", "analysis.json")
ASSETS_DIR = "assets"

DEFAULT_PALETTE = {"bg": "#0E141B", "text": "#E6E9ED", "accent": "#FF6A5A"}

DRY_RUN = "--dry-run" in sys.argv


def load_dotenv(path=".env"):
    """Minimal .env loader (no extra dependency): reads KEY=VALUE lines
    and puts them into os.environ if not already set."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_dotenv()


# ----------------------------------------------------------- prompt build --

def style_suffix(palette):
    """The shared 'look' applied to every image so the set feels like one
    deck, not five unrelated pictures. Driven by the deck's theme palette."""
    return (
        "Abstract, editorial illustration style. "
        f"Color palette: {palette['bg']} background, "
        f"{palette['text']} highlights, {palette['accent']} accent. "
        "Soft directional lighting, clean geometric composition. "
        "No text, no logos, no UI elements, no readable labels, "
        "no charts, no screens. 16:9 composition."
    )


def gap_prompt(gap, palette):
    return (
        "A wide isometric illustration for a direct-to-consumer beauty brand's "
        "e-commerce operations. "
        f"Show two separate platforms, each piled with stacks of cosmetic product "
        f"boxes and shipping labels, drifting apart over a dark cracked void. "
        f"Boxes and labels are scattering and falling into the gap between them. "
        f"A single thin cable connecting the platforms is fraying and sparking. "
        f"This represents the problem: \"{gap.get('gap', '')}\" — "
        f"{gap.get('why_it_matters', '')} "
        + style_suffix(palette)
        + " No people, no human figures, no laptops, no documents, no dashboards, "
          "no screens."
    )


def solution_prompt(sol, palette):
    return (
        "A wide isometric illustration for a direct-to-consumer beauty brand's "
        "e-commerce operations. "
        "Show stacks of cosmetic product boxes and shipping labels from multiple "
        "separate platforms now flowing along converging glowing paths into one "
        "unified central platform, arriving in neat organized rows. "
        f"This represents the solution: \"{sol.get('product', '')}\" — "
        f"{sol.get('how_it_helps', '')} "
        + style_suffix(palette)
        + " No people, no human figures, no laptops, no documents, no dashboards, "
          "no screens."
    )


# ------------------------------------------------------------- API calls --

def call_agnes_image_api(prompt):
    """Calls Agnes's OpenAI-compatible image endpoint and returns raw image
    bytes. Handles both possible response shapes (hosted URL or base64)."""
    api_key = os.environ.get("AGNES_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AGNES_API_KEY environment variable is not set. "
            "Export your key before running this script."
        )

    body = json.dumps({
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": "1792x1024",   # close to 16:9
        "n": 1,
    }).encode("utf-8")

    req = urllib.request.Request(
        url=f"{API_BASE}/images/generations",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8")

    result = json.loads(raw)
    item = result["data"][0]

    b64 = item.get("b64_json")
    url = item.get("url")

    if b64:
        return base64.b64decode(b64)
    if url:
        with urllib.request.urlopen(url, timeout=60) as img_resp:
            return img_resp.read()

    # Neither field had a usable value — show the actual shape so the
    # parsing above can be fixed to match Agnes's real response.
    raise RuntimeError(f"Unrecognized image response: {raw[:800]}")


def save_image(image_bytes, filename):
    path = os.path.join(ASSETS_DIR, filename)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return os.path.join("assets", filename)  # path as used inside index.html


# ----------------------------------------------------------------- driver --

def main():
    with open(ANALYSIS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    palette = (data.get("theme") or {}).get("palette") or DEFAULT_PALETTE

    tasks = []  # (label, prompt, target_dict, target_key, filename)

    for i, gap in enumerate(data.get("gaps", []), start=1):
        tasks.append((
            f"gap {i}: {gap.get('gap', '')[:60]}",
            gap_prompt(gap, palette),
            gap, "image", f"gap-{i}.jpg",
        ))

    for i, sol in enumerate(data.get("solution_mapping", []), start=1):
        tasks.append((
            f"solution {i}: {sol.get('product', '')}",
            solution_prompt(sol, palette),
            sol, "image", f"solution-{i}.jpg",
        ))

    if not tasks:
        print("No gaps or solutions found in analysis.json — nothing to generate.")
        return

    for label, prompt, target, key, filename in tasks:
        print(f"\n=== {label} ===")
        print(prompt)

        if DRY_RUN:
            continue

        try:
            image_bytes = call_agnes_image_api(prompt)
            rel_path = save_image(image_bytes, filename)
            target[key] = rel_path
            print(f"-> saved {rel_path}")
        except Exception as e:
            print(f"-> FAILED ({e}) — leaving '{key}' unset; deck will show a placeholder.")

        time.sleep(1)  # be gentle on rate limits

    if DRY_RUN:
        print("\nDry run only — analysis.json not modified.")
        return

    with open(ANALYSIS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nUpdated {ANALYSIS_PATH} with new image paths.")


if __name__ == "__main__":
    main()