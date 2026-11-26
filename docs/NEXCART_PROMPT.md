# NexCart — Master Build Prompt for Claude Opus

> **AI Supply-Chain Disruption Radar + Hyper-Personalised Restock Nudging Platform**
> Final Year Project Build Prompt

---

## How to Use This Prompt

Copy everything from **Section 0** onwards and paste it into a new Claude Opus (or Claude Sonnet 4.5+) conversation. The model will build the entire application file by file, printing `✓ complete` after each step.

---

## Section 0 — Project Identity

| Field | Value |
|---|---|
| App name | NexCart |
| Tagline | Predict shelf gaps before they happen. Recover demand through personalised offers. |
| Category | Retail AI / Supply-Chain Intelligence |
| Architecture | Agentic AI (two-layer: disruption + personalisation) |
| Academic level | Final year university project (B.Tech / M.Tech) |
| Submission | Cognizant AI Hackathon — themes: Supply Chain Resilience + Hyper-Personalisation |

---

## Section 1 — Tech Stack (mandatory, do not deviate)

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ with FastAPI |
| Agent framework | LangGraph (langgraph + langchain-aws) |
| LLM runtime | AWS Bedrock (model: `claude-opus-4-5` OR `anthropic.claude-3-5-sonnet-20241022-v2:0`) |
| Database | MongoDB Atlas (via motor — async driver) |
| Event bus | Amazon EventBridge (boto3) |
| Frontend | React 18 + Vite + TailwindCSS v3 |
| Charts | Recharts |
| Notifications | Firebase Cloud Messaging (push) + SMTP (email) |
| External APIs | NewsAPI, OpenWeatherMap, MarineTraffic (or mock) |
| Containerise | Docker + docker-compose |
| Env config | python-dotenv + `.env` file (all secrets here) |

---

## Section 2 — Repository Structure

Generate the complete file tree first, then build each file:

```
nexcart/
├── .env.example                  ← ALL environment variables here
├── .env                          ← gitignored, filled by user
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── main.py                   ← FastAPI app entry point
│   ├── config.py                 ← MongoDB + AWS + API key loader
│   ├── database/
│   │   ├── connection.py         ← MongoDB motor client + ping
│   │   ├── models.py             ← Pydantic models for all collections
│   │   └── collections.py       ← Collection name constants
│   ├── agents/
│   │   ├── disruption_agent.py  ← LangGraph Layer 1 agent
│   │   └── nudge_agent.py       ← LangGraph Layer 2 GenAI agent
│   ├── routers/
│   │   ├── skus.py              ← SKU CRUD + risk status endpoints
│   │   ├── disruptions.py       ← Disruption events endpoints
│   │   ├── nudges.py            ← Customer nudge endpoints
│   │   ├── signals.py           ← External API signal ingestion
│   │   └── dashboard.py         ← Aggregated dashboard stats
│   ├── services/
│   │   ├── news_service.py      ← NewsAPI integration
│   │   ├── weather_service.py   ← OpenWeatherMap integration
│   │   ├── shipping_service.py  ← MarineTraffic / mock service
│   │   ├── eventbridge.py       ← AWS EventBridge publisher
│   │   └── notification.py      ← Push + email sender
│   └── utils/
│       ├── logger.py
│       └── risk_scorer.py       ← Composite risk score calculator
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx               ← Router + layout shell
        ├── components/
        │   ├── Sidebar.jsx
        │   ├── TopBar.jsx
        │   ├── StatCard.jsx
        │   ├── RiskBadge.jsx
        │   ├── SKUTable.jsx
        │   ├── DisruptionFeed.jsx
        │   ├── NudgeCard.jsx
        │   └── MongoStatus.jsx   ← Live DB connection indicator
        └── pages/
            ├── Dashboard.jsx     ← Main overview page
            ├── SKURisk.jsx       ← SKU risk radar view
            ├── Signals.jsx       ← Live signal feed
            ├── Nudges.jsx        ← Customer nudge campaigns
            ├── Settings.jsx      ← MongoDB + API key config UI
            └── Analytics.jsx    ← Charts and trend analysis
```

---

## Section 3 — MongoDB Configuration (critical entry points)

All MongoDB connection logic must be in `backend/database/connection.py`. Expose a clear entry point at the top of the file:

```python
MONGODB_URI = os.getenv("MONGODB_URI")
# ↑ USER ENTRY POINT: paste your Atlas connection string in .env
```

Create these **5 MongoDB collections** with indexes:

### 1. `skus`
```
Fields : sku_id, name, category, supplier_country,
         current_stock, reorder_point, risk_score (0-100),
         risk_level (low/medium/high/critical), last_updated
Indexes: sku_id (unique), risk_level
```

### 2. `disruption_events`
```
Fields : event_id, source (news/weather/shipping),
         title, description, affected_regions,
         affected_sku_ids[], severity (1-5),
         predicted_impact_days, created_at
Indexes: created_at (desc), affected_sku_ids
```

### 3. `customer_profiles`
```
Fields : customer_id, name, email, push_token,
         purchase_history[{sku_id, quantity, date}],
         preferences{categories[], brands[]}
Indexes: customer_id (unique), email
```

### 4. `nudge_campaigns`
```
Fields : campaign_id, sku_id, customer_id,
         substitute_sku_id, offer_text, channel (push/email),
         status (pending/sent/opened/converted),
         sent_at, opened_at, revenue_recovered
Indexes: sku_id, status, sent_at
```

### 5. `signal_logs`
```
Fields : signal_id, source, raw_payload, processed_at,
         risk_delta, triggered_agent_run (bool)
Indexes: processed_at (desc)
```

> In `backend/config.py`, create a startup health-check function that pings MongoDB and prints connection status on app boot. The **Settings page** in the frontend must show a live green/red MongoDB connection indicator (`MongoStatus` component) by calling `GET /api/health/db`.

---

## Section 4 — Environment Variables (`.env.example`)

Generate a complete `.env.example` with every variable the app needs. Each variable must have an inline comment explaining it:

```env
# ── MongoDB ──────────────────────────────────────────────────────
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
MONGODB_DB_NAME=nexcart

# ── AWS Bedrock ───────────────────────────────────────────────────
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-opus-4-5

# ── AWS EventBridge ───────────────────────────────────────────────
EVENTBRIDGE_BUS_NAME=nexcart-events
EVENTBRIDGE_SOURCE=com.nexcart.signals

# ── External Signal APIs ──────────────────────────────────────────
NEWS_API_KEY=your_newsapi_key
OPENWEATHER_API_KEY=your_openweathermap_key
MARINE_TRAFFIC_API_KEY=your_marinetraffic_key

# ── Notifications ─────────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FIREBASE_SERVER_KEY=your_firebase_server_key

# ── App ───────────────────────────────────────────────────────────
APP_ENV=development
APP_SECRET_KEY=change_this_to_a_random_string
FRONTEND_URL=http://localhost:5173
BACKEND_PORT=8000
SIGNAL_POLL_INTERVAL_SECONDS=300
```

---

## Section 5 — Backend: Layer 1 Agent (Disruption Prediction)

**File:** `backend/agents/disruption_agent.py`

Build a LangGraph `StateGraph` with these nodes:

```
ingest_signals → analyse_risk → update_sku_scores
    → flag_at_risk_skus → publish_to_eventbridge
```

| Node | Logic |
|---|---|
| `ingest_signals` | Pull from `news_service`, `weather_service`, `shipping_service`. Return list of raw signals. |
| `analyse_risk` | Call AWS Bedrock (Claude) to parse signals, identify affected supplier regions, estimate disruption probability (0–1) and days until impact (1–30). Return JSON: `{sku_ids[], risk_delta, reasoning}` |
| `update_sku_scores` | Write updated `risk_score` + `risk_level` to MongoDB `skus` collection via motor. |
| `flag_at_risk_skus` | Query skus where `risk_level IN ['high', 'critical']`. Store in state. |
| `publish_to_eventbridge` | Emit a `DisruptionDetected` event for each flagged SKU. Trigger Layer 2 agent. |

> The agent must run on a schedule (APScheduler) every `SIGNAL_POLL_INTERVAL_SECONDS` seconds. Also expose a manual trigger via `POST /api/agents/run-disruption`.

---

## Section 6 — Backend: Layer 2 Agent (GenAI Personalisation)

**File:** `backend/agents/nudge_agent.py`

Triggered by EventBridge `DisruptionDetected` events or `POST /api/agents/run-nudge`.

```
load_at_risk_customers → find_substitutes
    → generate_offer_copy → dispatch_nudges → log_campaign
```

| Node | Logic |
|---|---|
| `load_at_risk_customers` | Query `customer_profiles` where `purchase_history` contains at-risk `sku_id`. Return list. |
| `find_substitutes` | Query `skus` for same category, `risk_level = 'low'`, stock above `reorder_point`. Return top 3. |
| `generate_offer_copy` | Call AWS Bedrock (Claude) with personalisation prompt (see below). Return JSON: `{subject, body, cta_text}` |
| `dispatch_nudges` | Choose channel by `push_token` presence. Call `notification.py`. Insert into `nudge_campaigns`. |
| `log_campaign` | Update campaign status + `revenue_recovered` after delivery confirmation. |

**Bedrock system prompt for `generate_offer_copy`:**

```
You are NexCart's personalisation engine. Given a customer's
purchase history and an at-risk product, write a warm, concise
personalised message (max 80 words) offering a substitute product.
Mention the customer's name, why they might need this now, and
make it feel helpful not alarming.
Return JSON: {subject, body, cta_text}

Inputs: customer_name, at_risk_sku_name, substitute_sku details,
last_purchase_date.
```

---

## Section 7 — REST API Endpoints

Implement all endpoints with proper `async/await`, error handling, and Pydantic response models.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | App status + version |
| GET | `/api/health/db` | MongoDB ping + latency ms |
| GET | `/api/dashboard/stats` | KPI summary: total SKUs, at-risk count, nudges sent today, revenue recovered 7d, signal events 24h |
| GET | `/api/skus` | Paginated list (risk sorted) |
| GET | `/api/skus/{sku_id}` | Single SKU + full risk history |
| POST | `/api/skus` | Create SKU |
| PATCH | `/api/skus/{sku_id}/risk` | Manually override risk level |
| GET | `/api/disruptions` | Recent events (last 50) |
| GET | `/api/signals/feed` | Live signal logs (SSE stream) |
| POST | `/api/signals/ingest` | Manually push a signal |
| GET | `/api/nudges` | All campaigns with status |
| GET | `/api/nudges/{campaign_id}` | Single campaign detail |
| POST | `/api/agents/run-disruption` | Trigger Layer 1 manually |
| POST | `/api/agents/run-nudge` | Trigger Layer 2 manually |
| GET | `/api/analytics/risk-trend` | 30-day risk score time series |
| GET | `/api/analytics/nudge-conversion` | Campaign conversion rates |
| GET | `/api/customers` | Paginated customer list |
| POST | `/api/customers` | Seed / create customer profile |

---

## Section 8 — Frontend: UI Design Language (non-negotiable)

Design a stunning, modern **dark-themed dashboard**. Reference: Linear.app, Vercel dashboard, and Shadcn/ui aesthetic.

### Design tokens (`tailwind.config.js`)

```js
colors: {
  bg: {
    base:  '#0A0A0F',   // near-black background
    card:  '#12121A',   // card surface
    hover: '#1A1A26',   // hover state
  },
  border:  '#1E1E2E',
  accent: {
    purple: '#7C6DDD',  // disruption signals
    teal:   '#1D9E75',  // safe / healthy SKUs
    amber:  '#EF9F27',  // medium risk
    danger: '#E24B4A',  // critical risk
  },
  text: {
    primary:   '#E8E8F0',
    secondary: '#6E6E8A',
  },
}
```

### Layout rules

- Fixed sidebar **240px** wide, collapsible to **60px** icon-only
- Top bar **56px** with live clock, MongoDB status dot, user avatar
- Main content: CSS grid, responsive (1 → 2 → 3 col cards)
- All cards: `background #12121A`, `border 1px solid #1E1E2E`, `border-radius 16px`, subtle inner glow on hover
- Risk levels as colour-coded pills: `low=teal`, `medium=amber`, `high=orange`, `critical=red (pulsing)`
- All numbers animate count-up on page load
- Skeleton loaders while data fetches

### Pages

| Page | Content |
|---|---|
| `Dashboard.jsx` | 4 KPI stat cards, risk distribution donut chart, live signal feed, top 5 at-risk SKUs table, recent nudges panel |
| `SKURisk.jsx` | Full SKU table with search + filter by risk/category. Rows expand to show risk history sparkline + linked disruption events |
| `Signals.jsx` | Real-time SSE feed of ingested signals with source icon, severity badge, affected SKU pills |
| `Nudges.jsx` | Campaign cards grid: status, channel icon, customer name, offer preview, open rate, revenue recovered |
| `Analytics.jsx` | Line chart: 30-day risk score trends. Bar chart: nudge conversion rates. KPI: total revenue protected this month |
| `Settings.jsx` | MongoDB URI form, live connection indicator (animated green/red dot), API key fields, agent scheduler toggle, "Test connection" button |

---

## Section 9 — Seed Data Script

**File:** `backend/scripts/seed.py`

Generate realistic seed data:

- **50 SKUs** across 5 categories (Electronics, Apparel, Food, Pharma, Home Goods) with randomised risk scores
- **200 customer profiles** with purchase histories
- **20 disruption events** (last 30 days)
- **100 nudge campaigns** with mixed statuses
- **500 signal log entries**

All dates relative to `datetime.now()`. Include CLI flag:

```bash
python seed.py --reset   # wipe and reseed
```

---

## Section 10 — Docker Setup

`docker-compose.yml` with 3 services:

| Service | Details |
|---|---|
| `nexcart-backend` | Python FastAPI on port `8000`, mounts `.env`, hot-reloads with `--reload` |
| `nexcart-frontend` | Vite dev server on port `5173`, proxies `/api` → `backend:8000` |
| `nexcart-mongo` | `mongo:7` image, port `27017`, volume `nexcart-mongo-data` (local fallback if Atlas not set) |

**Makefile commands:**

```makefile
make install   # pip install + npm install
make seed      # python seed.py
make dev       # docker-compose up
make build     # production build
```

---

## Section 11 — README.md

Write a professional `README.md` including:

1. Project overview + ASCII architecture diagram
2. Prerequisites (Python 3.11, Node 18, Docker)
3. MongoDB Atlas setup steps with screenshot placeholders
4. Step-by-step local setup (clone → `.env` → seed → run)
5. API documentation table
6. How the two AI agents work
7. Demo walkthrough (simulate a disruption in 3 steps)
8. Academic references (McKinsey, WEF, AWS docs)
9. Team / author section

---

## Section 12 — Build Order (follow exactly)

Complete each file **fully** before moving to the next. Do not ask for confirmation between steps.

| Step | File |
|---|---|
| 1 | `.env.example` (all variables, all comments) |
| 2 | `backend/database/connection.py` + `models.py` + `collections.py` |
| 3 | `backend/config.py` (load env, health check function) |
| 4 | `backend/services/` (all 5 service files) |
| 5 | `backend/agents/disruption_agent.py` (Layer 1) |
| 6 | `backend/agents/nudge_agent.py` (Layer 2) |
| 7 | `backend/routers/` (all 5 router files) |
| 8 | `backend/main.py` (mount routers, startup events) |
| 9 | `backend/scripts/seed.py` |
| 10 | `frontend/tailwind.config.js` + `vite.config.js` |
| 11 | `frontend/src/App.jsx` + `Sidebar` + `TopBar` components |
| 12 | `frontend/src/pages/` (all 6 pages, Dashboard first) |
| 13 | `frontend/src/components/` (all shared components) |
| 14 | `docker-compose.yml` + `Makefile` |
| 15 | `README.md` |

---

## Section 13 — Quality Requirements

### Backend
- All DB calls use `async/await` with `motor`
- Every endpoint has `try/except` with `HTTPException`
- Pydantic v2 models for all request/response shapes
- Logging via `backend/utils/logger.py` (structured JSON logs)
- No hardcoded credentials anywhere — always from `os.getenv()`
- MongoDB URI must come exclusively from `MONGODB_URI` env var

### Frontend
- No inline styles — Tailwind classes only
- Every data fetch uses React Query (`@tanstack/react-query`)
- Loading states: skeleton components (not spinners)
- Error states: friendly error cards with retry button
- All numbers formatted with `Intl.NumberFormat`
- Dark mode only (no light mode toggle needed)
- Responsive down to 768px tablet width

---

## Begin Building

> Paste this entire document into Claude Opus (or Claude Sonnet 4.5+).
> The model will start with Step 1 and print `✓ [filename] complete`
> after each file, then immediately proceed to the next step without
> asking for confirmation.

---

*NexCart — Final Year Project | AI Supply-Chain Disruption Radar*
*Built with Claude Opus · LangGraph · AWS Bedrock · MongoDB Atlas*
