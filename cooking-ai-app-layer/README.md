# cooking-ai-app-layer

The **Application Layer** — sits between your frontend (Presentation
Layer) and the `cooking_ai_data_layer` package (Data/Model Layer).
Its only jobs: validate HTTP input, call the data layer, shape JSON
responses, handle errors. No recipe/search/model logic lives here.

## Request flow

```
Frontend (browser/mobile)
    │  fetch('/api/search?q=margayta+pizza')
    ▼
Application Layer (this folder)         <- validates 'q' is present
    │  model_layer.search("margayta pizza")
    ▼
Data/Model Layer (cooking_ai_data_layer) <- fuzzy+semantic match, local LLM, YouTube
    │
    ▼
JSON response → back up through Application Layer → Frontend
```

## Connecting to the Data/Model Layer

This is the entire connection — one line, in `app/__init__.py`:

```python
from cooking_ai_data_layer import CookingDataModelLayer
app.extensions["model_layer"] = CookingDataModelLayer()
```

Built once at startup, reused for every request. Routes pull it via
`current_app.extensions["model_layer"]` rather than a global import,
which is what makes it trivial to swap in a fake for tests
(see `tests/test_routes.py`).

## Setup

```bash
# 1. Install the data layer (from the previous step)
pip install -e ../cooking-ai-data-layer

# 2. Install this layer's own dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env   # set YOUTUBE_API_KEY

# 4. Run
python run.py          # dev server on :5000
# or
gunicorn --preload run:app   # production
```

## API

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| GET | `/api/search?q=...&videos=4` | — | matched recipe + ingredients + steps + videos |
| POST | `/api/ask` | `{"query": "...", "question": "..."}` | grounded answer from the local model |
| POST | `/api/substitute` | `{"query": "...", "ingredient": "..."}` | substitution from the knowledge base |
| GET | `/health` | — | `{"status": "ok"}` |

A missing required field returns `400`. A query that doesn't match
any recipe returns `404` with `{"found": false, ...}`.

## Connecting the Presentation Layer (frontend)

Any frontend just calls these endpoints over HTTP. Example:

```javascript
async function searchRecipe(query) {
  const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  return res.json();
  // { found, matched_title, confidence, recipe: {ingredients, steps}, videos }
}
```

If the frontend runs on a different origin/port during development,
`flask-cors` (already wired in `app/__init__.py`) handles that —
just make sure it's installed.

## Testing without the real models loaded

`tests/test_routes.py` injects a fake model layer with the same
method signatures as `CookingDataModelLayer`, so you can verify
routing, validation, and status codes instantly — no waiting on
model downloads:

```bash
python -m unittest tests/test_routes.py -v
```

## Docker (both layers together)

Build context must have both folders as siblings:

```
.
├── cooking-ai-app-layer/    (this folder)
└── cooking-ai-data-layer/   (from the previous step)
```

```bash
docker build -f cooking-ai-app-layer/Dockerfile -t cooking-ai-app .
docker run -p 5000:5000 --env-file cooking-ai-app-layer/.env cooking-ai-app
```

## Production notes

- `--preload` in the gunicorn command loads the embedding + LLM models
  once in the master process before forking workers, instead of once
  per worker — important since model loading is the expensive part.
- The first request after a cold start may be slow (one-time model
  download/load); the Dockerfile sets a generous `--timeout 120` to
  cover that.
- Put a cache (Redis) in front of `/api/search` for popular queries
  in a real deployment — that's a Data/Model Layer change
  (`CookingDataModelLayer.search`), not something this layer needs to
  know about.
