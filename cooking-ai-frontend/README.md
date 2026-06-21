# cooking-ai-frontend

The **Presentation Layer** — a static HTML/CSS/JS site, no build step,
no framework. Talks only to the Application Layer's REST API.

## Design concept

Grounded in a real kitchen detail rather than a generic "recipe app"
look: when a line cook fires an order, it prints out as a ticket. The
search result here is built the same way — a printed kitchen docket
with a torn perforated edge, a ticket number, and ingredient amounts
set in a monospace face like a thermal printer. Dark stainless-steel
background, warm tomato/char-orange accents pulled from the food
itself rather than a decorative palette.

| Role | Typeface |
|---|---|
| Display (headlines, ticket title) | Big Shoulders Display — condensed, stamped/industrial |
| Body | Albert Sans |
| Data (quantities, tags, labels) | Space Mono — the "receipt printer" voice |

## Files

```
cooking-ai-frontend/
├── index.html
├── css/style.css
└── js/
    ├── config.js   # the one line you change to point at your API
    └── app.js      # all fetch calls + DOM rendering
```

No build tools, no npm install — open `index.html` in a browser or
serve the folder with any static file server.

## Connecting to the Application Layer

One file, one constant — `js/config.js`:

```javascript
const API_BASE_URL = 'http://localhost:5000';
```

The frontend calls exactly three endpoints, matching the Application
Layer built in the previous step:

- `GET  /api/search?q=...&videos=4` — on search submit or example chip click
- `POST /api/ask` — from the "Ask the line cook" box
- `POST /api/substitute` — from the "Need a swap?" box

If you serve this frontend from the Flask app itself (same origin),
set `API_BASE_URL = ''` instead and you won't need CORS at all.

## Running the full stack locally

```bash
# Terminal 1 — data + app layers
pip install -e cooking-ai-data-layer
pip install -r cooking-ai-app-layer/requirements.txt
cd cooking-ai-app-layer && python run.py        # serves API on :5000

# Terminal 2 — frontend
cd cooking-ai-frontend && python3 -m http.server 8080
```

Open `http://localhost:8080`, search "margayta pizza", and the whole
chain runs: frontend → Application Layer → Data/Model Layer (local
embedding search + local LLM + YouTube) → back up to the ticket on
screen.

## Notes on what's real vs. cosmetic

- The ticket number (`#047` etc.) is decorative flavor text generated
  client-side — it has no backend meaning, just reinforces the kitchen
  metaphor.
- Everything else on the ticket (title, tags, servings, ingredients,
  steps) comes directly from the `/api/search` response — nothing is
  hardcoded.

## Accessibility / robustness

- Visible focus rings on every interactive element (`:focus-visible`).
- `prefers-reduced-motion` disables the ticket print-in animation and
  all transitions.
- Search, ask, and substitute all have loading and error states —
  network failures show a plain-language message instead of a silent
  failure.
- Semantic HTML throughout (`<form>`, `<label>`, `aria-live` regions
  for dynamic content) so screen readers announce new results.
