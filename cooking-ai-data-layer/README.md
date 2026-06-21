# cooking-ai-data-layer

The **Data/Model Layer** of the 3-tier cooking AI architecture, packaged
as a real installable Python module — `pip install` it once and any
other project (your Presentation layer's backend, your Application
layer, a separate microservice) can import it directly.

## No hosted LLM APIs

Every model here is open-source and runs locally in your own process
via Hugging Face's `transformers` / `sentence-transformers` — no calls
to Claude, ChatGPT, Gemini, or any other hosted model API.

| Task | Model | Why |
|---|---|---|
| Recipe search (typo + intent tolerant) | `all-MiniLM-L6-v2` | 22M params, fast on CPU |
| Explanations / follow-up Q&A | `google/flan-t5-base` | Instruction-tuned, Apache-2.0, runs on CPU |
| Ingredient substitutions | Curated JSON knowledge base, model as fallback | Deterministic beats hallucinated |
| Video lookup | YouTube Data API v3 (public search) | No user OAuth needed |

## Project layout

```
cooking-ai-data-layer/
├── pyproject.toml                  # makes this `pip install`-able
├── requirements.txt                # same deps, plain-file form
├── .env.example                    # copy to .env and fill in
├── cooking_ai_data_layer/          # <-- the actual importable package
│   ├── __init__.py                 # public API: CookingDataModelLayer
│   ├── config.py                   # centralized env-var settings
│   ├── embedding_search.py
│   ├── local_llm_service.py
│   ├── youtube_service.py
│   ├── data_model_layer.py         # the facade class
│   └── data/
│       ├── recipes.json
│       └── substitutions.json
├── examples/
│   └── app_layer_example.py        # Flask app consuming the installed package
└── tests/
    └── test_integration.py         # smoke tests, no network required
```

## Install (this is the integration step)

From the **Application Layer's** project, or in the shared virtualenv
both layers use:

```bash
pip install -e /path/to/cooking-ai-data-layer
cp /path/to/cooking-ai-data-layer/.env.example .env
# edit .env — only YOUTUBE_API_KEY is required for real video results
```

That's it. From anywhere in that environment:

```python
from cooking_ai_data_layer import CookingDataModelLayer

model_layer = CookingDataModelLayer()   # build once at app startup

model_layer.search("margayta pizza")
model_layer.ask_followup("margherita pizza", "no pizza stone, what do I do?")
model_layer.substitution("margherita pizza", "mozzarella")
```

`search()` returns one dict with everything the Presentation Layer
needs to render: matched title, confidence score, full recipe
(ingredients + steps), and a list of videos — no further data
wrangling needed on the frontend side. See `examples/app_layer_example.py`
for the exact Flask routes that wrap these three methods.

## Configuration

All settings live in `.env` (loaded automatically by `config.py`) —
no hand-wiring keys into constructor calls:

```
YOUTUBE_API_KEY=...
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2     # optional override
LOCAL_LLM_MODEL_NAME=google/flan-t5-base  # optional override
SEARCH_MIN_CONFIDENCE=0.35
DEFAULT_VIDEO_COUNT=4
```

## Verifying the install

```bash
python tests/test_integration.py
# or: pytest tests/
```

These tests deliberately avoid triggering real model downloads — they
check package structure, recipe data integrity, and the deterministic
substitution-lookup path, so they pass even before the ML model
weights have been downloaded.

The first real `search()` or `ask_followup()` call will trigger a
one-time model download (~90MB embedding model, ~250MB Flan-T5-base).
After that, everything runs locally with no further downloads.

## Scaling this to real-world size

- **Recipe data**: `data/recipes.json` ships with 6 sample recipes.
  Replace with your real dataset — the loader just expects the same
  JSON shape (`title`, `tags`, `ingredients`, `steps`).
- **Vector index**: in-memory cosine similarity is fine for thousands
  of recipes; past that, swap in FAISS or a hosted vector DB inside
  `RecipeSearchIndex` — the `search()`/`best_match()` interface that
  the rest of the system depends on doesn't change.
- **Local model quality**: bump `LOCAL_LLM_MODEL_NAME` to
  `google/flan-t5-large` or `-xl` if you have a GPU.
- **Caching**: put Redis in front of `CookingDataModelLayer.search()`
  for popular queries — margherita pizza will be searched constantly.
