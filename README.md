# Cooking AI — full three-layer project

A complete, working implementation: search a dish (typos welcome),
get the recipe, the method, relevant videos, and an AI line cook for
follow-up questions and ingredient swaps. No hosted LLM APIs anywhere
in the stack — every model runs locally.

```
cooking-ai-project/
├── cooking-ai-data-layer/   Layer 3 — recipe search, local LLM, YouTube lookup
├── cooking-ai-app-layer/    Layer 2 — Flask REST API wrapping the data layer
└── cooking-ai-frontend/     Layer 1 — the UI a person actually uses
```

Each folder has its own README with full detail. This file is just
the map and the fastest path to running all three together.

## Architecture

```
┌─────────────────────┐     fetch()      ┌──────────────────────┐    Python import   ┌──────────────────────────┐
│  cooking-ai-frontend │ ───────────────▶ │  cooking-ai-app-layer │ ─────────────────▶ │  cooking-ai-data-layer    │
│  (HTML/CSS/JS, no    │ ◀─────────────── │  (Flask REST API)     │ ◀───────────────── │  (embedding search +     │
│   build step)        │      JSON        │                       │   recipe/videos/    │   local LLM + YouTube)   │
└─────────────────────┘                  └──────────────────────┘   answer dicts       └──────────────────────────┘
```

Each layer only knows about the one directly below it. The frontend
has never heard of Hugging Face or YouTube — it just calls
`/api/search`. The app layer has never heard of sentence-transformers
or Flan-T5 — it just calls `model_layer.search(query)`.

## Run everything

```bash
# 1. Data/Model Layer
pip install -e cooking-ai-data-layer

# 2. Application Layer
pip install -r cooking-ai-app-layer/requirements.txt
cp cooking-ai-app-layer/.env.example cooking-ai-app-layer/.env
# edit .env, set YOUTUBE_API_KEY
cd cooking-ai-app-layer && python run.py &
cd ..

# 3. Presentation Layer
cd cooking-ai-frontend && python3 -m http.server 8080
```

Open `http://localhost:8080`, search "margayta pizza" (typo
intentional), and the full chain runs end to end.

## What's been verified vs. what needs your environment

Verified in development:
- The Application Layer's routing, validation, and error handling
  (`cooking-ai-app-layer/tests/test_routes.py` — 7/7 passing)
- The Data Layer's package installation, imports from outside its own
  folder, and substitution knowledge-base logic
  (`cooking-ai-data-layer/tests/test_integration.py` — passing)
- A real Flask server responding correctly over HTTP to
  `/api/search`, matching exactly what the frontend's `fetch` calls expect
- The frontend's visual design and responsive layout, rendered and
  reviewed at desktop and mobile widths

Needs your environment (this build environment has no internet
access, so these couldn't be exercised live):
- The actual embedding model (`all-MiniLM-L6-v2`) and local LLM
  (`google/flan-t5-base`) — these download from Hugging Face on first
  use, after `pip install -e cooking-ai-data-layer`
- Real YouTube search results — needs a `YOUTUBE_API_KEY`
- The frontend's JavaScript fetch calls against a live backend in an
  actual browser (the design was reviewed visually; the request/
  response contract was verified via the Flask test client and a
  live HTTP server instead)

## Adding your own recipes

Everything flows from one file:
`cooking-ai-data-layer/cooking_ai_data_layer/data/recipes.json`. Add
entries in the same shape (title, tags, servings, ingredients, steps)
and they're searchable immediately — no other layer needs to change.
