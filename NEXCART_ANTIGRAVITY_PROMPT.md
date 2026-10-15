# NexCart — Antigravity Phased Build Prompt
## Complete Phase-by-Phase Instructions for Claude Opus

> **Reference document:** `NEXCART_PROMPT.md` (attach this file to every phase conversation)
> **Model:** Claude Opus (claude-opus-4-5) via Antigravity
> **Strategy:** One Antigravity conversation per phase. Always attach `NEXCART_PROMPT.md`.

---

## How to Use This Document

1. Open Antigravity and start a **new conversation**
2. **Attach** `NEXCART_PROMPT.md` to the conversation
3. Copy the prompt for **Phase 1** below and send it
4. Wait for all files to be generated and confirmed
5. Download / copy the output files to your local project
6. Start a **new conversation** for Phase 2, attach the same MD file, repeat
7. Never skip a phase — each phase depends on the previous one

---

---

# ═══════════════════════════════════════════════════════
# PHASE 1 — PROJECT SCAFFOLD & ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════

**Paste this into Antigravity (with NEXCART_PROMPT.md attached):**

```
You are Claude Opus, a senior full-stack engineer building NexCart —
an AI supply-chain disruption radar for a final year university project.

I have attached NEXCART_PROMPT.md which is the complete specification
document for this project. Read it fully before writing any code.

Your task in this phase is ONLY the project scaffold and environment setup.
Do not build any logic yet — only structure, config, and environment files.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 DELIVERABLES (build all of these, fully, in order):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1.1 — .env.example
  Build the complete .env.example file exactly as specified in
  Section 4 of the attached MD. Every variable must have an inline
  comment. Cover all 5 groups: MongoDB, AWS Bedrock, EventBridge,
  External APIs, Notifications, App config.
  Print "✓ .env.example complete" when done.

STEP 1.2 — .gitignore
  Create a proper Python + Node.js .gitignore. Must include:
  .env, __pycache__, node_modules, dist, .vite, *.pyc,
  .DS_Store, venv/, .pytest_cache, *.egg-info
  Print "✓ .gitignore complete" when done.

STEP 1.3 — backend/requirements.txt
  List every Python package needed for the full project:
  fastapi, uvicorn[standard], motor, pydantic>=2.0, python-dotenv,
  boto3, langchain, langchain-aws, langgraph, apscheduler,
  httpx, aiosmtplib, requests, pytest, pytest-asyncio
  Pin realistic versions. Print "✓ requirements.txt complete" when done.

STEP 1.4 — frontend/package.json
  Create a complete package.json for React 18 + Vite + Tailwind.
  Dependencies must include: react, react-dom, react-router-dom,
  @tanstack/react-query, recharts, axios, clsx, lucide-react.
  DevDependencies: vite, @vitejs/plugin-react, tailwindcss,
  postcss, autoprefixer. Include scripts: dev, build, preview.
  Print "✓ package.json complete" when done.

STEP 1.5 — frontend/vite.config.js
  Configure Vite with React plugin. Add a proxy rule:
  /api → http://localhost:8000 (so frontend calls hit the backend).
  Print "✓ vite.config.js complete" when done.

STEP 1.6 — frontend/tailwind.config.js
  Implement the FULL design token system from Section 8 of the MD:
  bg.base=#0A0A0F, bg.card=#12121A, bg.hover=#1A1A26,
  border=#1E1E2E, accent.purple=#7C6DDD, accent.teal=#1D9E75,
  accent.amber=#EF9F27, accent.danger=#E24B4A,
  text.primary=#E8E8F0, text.secondary=#6E6E8A.
  Add Inter font via fontFamily. Content: ['./src/**/*.{js,jsx}'].
  Print "✓ tailwind.config.js complete" when done.

STEP 1.7 — frontend/index.html
  Clean HTML5 boilerplate. Link Inter from Google Fonts.
  Mount point: <div id="root">. Dark background on body (#0A0A0F).
  Print "✓ index.html complete" when done.

STEP 1.8 — docker-compose.yml
  Build the 3-service docker-compose as specified in Section 10
  of the MD: nexcart-backend (port 8000), nexcart-frontend
  (port 5173), nexcart-mongo (port 27017, volume nexcart-mongo-data).
  All services in a shared network. Backend depends_on mongo.
  Print "✓ docker-compose.yml complete" when done.

STEP 1.9 — Makefile
  Add these targets: install, seed, dev, build, lint, clean.
  Each target must print what it is doing.
  Print "✓ Makefile complete" when done.

STEP 1.10 — backend/__init__.py and all empty __init__.py files
  Create empty __init__.py files for: backend/, backend/database/,
  backend/agents/, backend/routers/, backend/services/, backend/utils/
  Print "✓ __init__.py files complete" when done.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Output every file as a complete fenced code block with the
  filename as the label, e.g.: ```python backend/config.py
- Do not summarise or truncate any file. Every file must be
  100% complete and copy-pasteable.
- After all 10 steps, print a Phase 1 summary table showing
  every file created and its line count.
- End with: "PHASE 1 COMPLETE — ready for Phase 2"
```

---

---

# ═══════════════════════════════════════════════════════
# PHASE 2 — DATABASE LAYER (MongoDB + Pydantic Models)
# ═══════════════════════════════════════════════════════

**Start a NEW Antigravity conversation. Attach NEXCART_PROMPT.md. Paste this:**

```
You are Claude Opus building NexCart. The attached NEXCART_PROMPT.md
is the full specification. Phase 1 (scaffold) is already complete.

Your task in this phase is ONLY the database layer.
Build every file completely. Do not write placeholder or TODO code.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 DELIVERABLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2.1 — backend/database/collections.py
  Define string constants for all 5 collection names:
  SKUS, DISRUPTION_EVENTS, CUSTOMER_PROFILES,
  NUDGE_CAMPAIGNS, SIGNAL_LOGS.
  Print "✓ collections.py complete" when done.

STEP 2.2 — backend/database/models.py
  Build complete Pydantic v2 models for all 5 collections
  as defined in Section 3 of the MD. Requirements:
  - Use Field() with description and default values
  - Use datetime for all date fields (with timezone=True)
  - Use Enum classes for: RiskLevel, NudgeChannel, NudgeStatus,
    SignalSource, DisruptionSeverity
  - Add a Config class to each model with populate_by_name=True
  - Build both a base model (for creation) and a full model
    (with id field) for each collection
  - Add a helper to_dict() method that converts ObjectId to string
  Models to build:
    SKUBase, SKUModel, SKUResponse
    DisruptionEventBase, DisruptionEventModel, DisruptionEventResponse
    CustomerProfileBase, CustomerProfileModel, CustomerProfileResponse
    NudgeCampaignBase, NudgeCampaignModel, NudgeCampaignResponse
    SignalLogBase, SignalLogModel, SignalLogResponse
  Print "✓ models.py complete" when done.

STEP 2.3 — backend/database/connection.py
  Build the full async MongoDB connection using motor.
  Requirements (all from Section 3 of the MD):
  - MONGODB_URI loaded from os.getenv("MONGODB_URI") — this is the
    USER ENTRY POINT. Add a clear comment: # USER ENTRY POINT
  - MONGODB_DB_NAME loaded from os.getenv("MONGODB_DB_NAME", "nexcart")
  - Async function: connect_to_mongo() — call on app startup
  - Async function: close_mongo_connection() — call on app shutdown
  - Async function: ping_database() → returns {"status": "ok",
    "latency_ms": float} or {"status": "error", "detail": str}
  - Create all 5 collections with their indexes on first connect:
    skus: unique index on sku_id, regular on risk_level
    disruption_events: descending on created_at, on affected_sku_ids
    customer_profiles: unique on customer_id, regular on email
    nudge_campaigns: regular on sku_id, status, sent_at
    signal_logs: descending on processed_at
  - Expose a db global variable accessible from other modules
  - Handle ConnectionFailure with a clear error message telling
    the user to check their MONGODB_URI in .env
  Print "✓ connection.py complete" when done.

STEP 2.4 — backend/config.py
  Central config loader using pydantic-settings or python-dotenv.
  Build a Settings class with all env vars as typed attributes.
  Include a startup_health_check() async function that:
  - Pings MongoDB and logs the result
  - Checks AWS credentials are present
  - Prints a startup banner with app name, version, environment
  Print "✓ config.py complete" when done.

STEP 2.5 — backend/utils/logger.py
  Structured JSON logger using Python's logging module.
  - Log format: {"timestamp": ..., "level": ..., "module": ...,
    "message": ..., "extra": ...}
  - Expose a get_logger(name) function used by all other modules
  - Log to stdout in development, to file in production
  Print "✓ logger.py complete" when done.

STEP 2.6 — backend/utils/risk_scorer.py
  Build a RiskScorer class with a method:
    calculate_risk_score(signals: list, sku: dict) → int (0-100)
  Logic:
  - Base score from sku.current_stock vs sku.reorder_point ratio
  - Add signal_weight based on signal severity and source type
  - Cap at 100, floor at 0
  - Return risk_level string based on score:
    0-25=low, 26-50=medium, 51-75=high, 76-100=critical
  Print "✓ risk_scorer.py complete" when done.

STEP 2.7 — backend/scripts/seed.py
  Full seed script as specified in Section 9 of the MD.
  Generate:
  - 50 SKUs across 5 categories with realistic names and
    randomised risk scores, supplier_country from real countries
  - 200 customer profiles with realistic names, emails,
    purchase_history referencing the seeded SKU ids
  - 20 disruption events linked to real seeded SKUs
  - 100 nudge campaigns referencing seeded SKUs and customers
  - 500 signal log entries across last 30 days
  All dates must be realistic (relative to datetime.now()).
  CLI: python seed.py --reset wipes all collections before seeding.
  Print progress to console: "Seeding SKUs... done (50)"
  Print "✓ seed.py complete" when done.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Every async function must be properly awaited
- No hardcoded credentials — everything from os.getenv()
- All Pydantic models must use v2 syntax (model_config, not class Config)
- Every file must be 100% complete with no TODOs or placeholders
- After all steps, print: "PHASE 2 COMPLETE — ready for Phase 3"
```

---

---

# ═══════════════════════════════════════════════════════
# PHASE 3 — EXTERNAL SERVICES & AGENT LAYER
# ═══════════════════════════════════════════════════════

**Start a NEW Antigravity conversation. Attach NEXCART_PROMPT.md. Paste this:**

```
You are Claude Opus building NexCart. The attached NEXCART_PROMPT.md
is the full specification. Phases 1 and 2 are complete.

Your task in this phase is the external services and both AI agents.
This is the most critical phase. Read Sections 5 and 6 of the MD
carefully before writing any agent code.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 DELIVERABLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3.1 — backend/services/news_service.py
  Build a NewsService class with method:
    async fetch_signals() → list[dict]
  Integration: NewsAPI (https://newsapi.org/v2/everything)
  Query terms: ["supply chain disruption", "port strike",
    "shipping delay", "factory closure", "trade tariff"]
  Parse response into normalised signal dicts:
    {source: "news", title, description, severity: int(1-5),
     affected_regions: [], published_at: datetime}
  Severity scoring: keyword match on "critical/closure/strike"=5,
  "delay/disruption"=3, "shortage/risk"=2, else=1.
  If NEWS_API_KEY is missing, return 3 realistic mock signals.
  Print "✓ news_service.py complete" when done.

STEP 3.2 — backend/services/weather_service.py
  Build a WeatherService class with method:
    async fetch_signals() → list[dict]
  Integration: OpenWeatherMap API (current weather + alerts)
  Monitor these supplier regions by default:
    Shanghai, Mumbai, Rotterdam, Los Angeles, Jakarta
  Return normalised signal dicts with source="weather".
  Severity: wind_speed>20m/s=5, heavy rain=3, mild storm=2.
  If OPENWEATHER_API_KEY is missing, return 3 mock weather signals.
  Print "✓ weather_service.py complete" when done.

STEP 3.3 — backend/services/shipping_service.py
  Build a ShippingService class with method:
    async fetch_signals() → list[dict]
  Integration: MarineTraffic API (or full mock if key missing).
  Monitor major shipping lanes: Strait of Malacca, Suez Canal,
  Panama Canal, English Channel, Taiwan Strait.
  Return normalised signal dicts with source="shipping".
  Always return 5 mock signals if MARINE_TRAFFIC_API_KEY is missing.
  Mock signals must be realistic: vessel names, coordinates,
  delay hours, affected ports.
  Print "✓ shipping_service.py complete" when done.

STEP 3.4 — backend/services/eventbridge.py
  Build an EventBridgeService class with method:
    async publish_disruption_event(sku_id, risk_score,
      risk_level, reasoning) → bool
  Use boto3 EventBridge client.
  Event structure:
    Source: EVENTBRIDGE_SOURCE env var
    DetailType: "DisruptionDetected"
    Detail: JSON with sku_id, risk_score, risk_level,
            reasoning, timestamp
    EventBusName: EVENTBRIDGE_BUS_NAME env var
  If AWS credentials are missing, log a warning and return True
  (graceful degradation so the app works without AWS in dev).
  Print "✓ eventbridge.py complete" when done.

STEP 3.5 — backend/services/notification.py
  Build a NotificationService class with two methods:
    async send_push(push_token, title, body, data) → bool
    async send_email(to_email, subject, body, cta_text) → bool
  Push: Use Firebase Cloud Messaging (FCM) REST API v1.
  Email: Use aiosmtplib with HTML email template.
    Email template must be a proper HTML email with:
    - NexCart branding header (dark purple #7C6DDD)
    - Offer body text
    - CTA button (teal #1D9E75)
    - Unsubscribe footer
  Graceful degradation: if keys are missing, log the
  notification content to console and return True.
  Print "✓ notification.py complete" when done.

STEP 3.6 — backend/agents/disruption_agent.py
  Build the Layer 1 LangGraph disruption prediction agent
  EXACTLY as specified in Section 5 of the attached MD.
  Requirements:
  - Use langgraph StateGraph with a typed State dataclass
  - 5 nodes: ingest_signals, analyse_risk, update_sku_scores,
    flag_at_risk_skus, publish_to_eventbridge
  - analyse_risk node must call AWS Bedrock using langchain-aws
    ChatBedrock with model from BEDROCK_MODEL_ID env var
  - The Bedrock prompt must instruct the model to return
    structured JSON: {affected_sku_ids[], risk_delta, reasoning,
    estimated_impact_days, confidence_score}
  - update_sku_scores must write to MongoDB skus collection
    using motor (async)
  - Wrap agent in a run_disruption_agent() async function
  - Add APScheduler AsyncIOScheduler that runs the agent every
    SIGNAL_POLL_INTERVAL_SECONDS seconds on app startup
  - Expose a manual trigger endpoint (imported by router)
  - Full error handling: if Bedrock is unavailable, use the
    RiskScorer heuristic as fallback
  Print "✓ disruption_agent.py complete" when done.

STEP 3.7 — backend/agents/nudge_agent.py
  Build the Layer 2 LangGraph personalisation agent
  EXACTLY as specified in Section 6 of the attached MD.
  Requirements:
  - Use langgraph StateGraph with a typed State dataclass
  - 5 nodes: load_at_risk_customers, find_substitutes,
    generate_offer_copy, dispatch_nudges, log_campaign
  - generate_offer_copy must call AWS Bedrock with this
    exact system prompt:
    "You are NexCart's personalisation engine. Given a
     customer's purchase history and an at-risk product,
     write a warm, concise personalised message (max 80 words)
     offering a substitute product. Mention the customer's
     name, why they might need this now, and make it feel
     helpful not alarming. Return ONLY valid JSON:
     {subject: string, body: string, cta_text: string}"
  - dispatch_nudges must pick channel by push_token presence:
    if push_token exists → send_push, else → send_email
  - log_campaign must insert into nudge_campaigns collection
    with status="sent" and sent_at=datetime.now()
  - Wrap in run_nudge_agent(sku_ids: list[str]) async function
  - Full error handling at every node
  Print "✓ nudge_agent.py complete" when done.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Every service must have graceful degradation (mock data
  if API key is missing). The app must run in demo mode
  without any real API keys.
- All MongoDB calls must use motor async — no sync calls.
- The Bedrock call in each agent must include retry logic
  (3 attempts, exponential backoff).
- After all steps: "PHASE 3 COMPLETE — ready for Phase 4"
```

---

---

# ═══════════════════════════════════════════════════════
# PHASE 4 — REST API ROUTERS & FASTAPI APP
# ═══════════════════════════════════════════════════════

**Start a NEW Antigravity conversation. Attach NEXCART_PROMPT.md. Paste this:**

```
You are Claude Opus building NexCart. The attached NEXCART_PROMPT.md
is the full specification. Phases 1, 2, and 3 are complete.

Your task in this phase is the full FastAPI REST API layer —
all routers, middleware, and the main app entry point.
Every endpoint from Section 7 of the MD must be implemented.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 DELIVERABLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4.1 — backend/routers/dashboard.py
  Implement these endpoints:
    GET /api/health          → {status, version, environment}
    GET /api/health/db       → {status, latency_ms} using ping_database()
    GET /api/dashboard/stats → aggregate stats from all collections:
      total_skus: count of skus collection
      at_risk_count: count where risk_level IN [high, critical]
      nudges_sent_today: count nudge_campaigns where sent_at >= today
      revenue_recovered_7d: sum of revenue_recovered last 7 days
      signal_events_24h: count signal_logs last 24 hours
      risk_distribution: {low: N, medium: N, high: N, critical: N}
  All queries must be async motor aggregations.
  Print "✓ dashboard.py router complete" when done.

STEP 4.2 — backend/routers/skus.py
  Implement:
    GET  /api/skus              → paginated list, sorted by risk_score desc
                                  Query params: page, limit, category,
                                  risk_level, search (name contains)
    GET  /api/skus/{sku_id}     → full SKU doc + last 10 disruption events
                                  that reference this sku_id
    POST /api/skus              → create new SKU, validate with SKUBase model
    PATCH /api/skus/{sku_id}/risk → override risk_level and risk_score,
                                    log the manual override to signal_logs
  Return proper 404 when SKU not found.
  Print "✓ skus.py router complete" when done.

STEP 4.3 — backend/routers/disruptions.py
  Implement:
    GET /api/disruptions       → last 50 events, sorted by created_at desc
                                 Filter params: source, severity_min,
                                 affected_region, sku_id
    GET /api/disruptions/{id}  → single event
    POST /api/disruptions      → manually create a disruption event
  Print "✓ disruptions.py router complete" when done.

STEP 4.4 — backend/routers/signals.py
  Implement:
    GET  /api/signals/feed      → Server-Sent Events (SSE) stream
                                  Use fastapi.responses.StreamingResponse
                                  Stream new signal_logs in real time
                                  (poll MongoDB every 2 seconds for new docs)
    POST /api/signals/ingest    → manually submit a signal payload,
                                  runs through the disruption agent
    GET  /api/signals/history   → paginated signal_logs, newest first
  Print "✓ signals.py router complete" when done.

STEP 4.5 — backend/routers/nudges.py
  Implement:
    GET  /api/nudges            → all nudge campaigns, paginated
                                  Filter: status, channel, sku_id, date range
    GET  /api/nudges/{id}       → single campaign with full detail
    PATCH /api/nudges/{id}/status → update status (opened, converted)
    GET  /api/analytics/nudge-conversion → conversion funnel:
                                  {sent, opened, converted} counts + rates
    GET  /api/analytics/risk-trend → 30-day time series:
                                  [{date, avg_risk_score, at_risk_count}]
    POST /api/agents/run-disruption → trigger Layer 1 agent manually,
                                      return {job_id, started_at, status}
    POST /api/agents/run-nudge     → trigger Layer 2 agent manually,
                                      body: {sku_ids: []}
    GET  /api/customers         → paginated customer list
    POST /api/customers         → create customer profile
  Print "✓ nudges.py router complete" when done.

STEP 4.6 — backend/main.py
  Build the main FastAPI application entry point. Requirements:
  - App title: "NexCart API", version: "1.0.0"
  - Add CORSMiddleware: allow origins from FRONTEND_URL env var
    and http://localhost:5173
  - Lifespan context manager (not deprecated on_event):
    startup: call connect_to_mongo(), startup_health_check(),
             start APScheduler for disruption agent
    shutdown: close_mongo_connection(), stop scheduler
  - Mount all 5 routers with prefix /api
  - Add a global exception handler for unhandled errors:
    return {error: str(exc), timestamp: ...} with 500 status
  - Add request logging middleware that logs method, path,
    status_code, duration_ms for every request
  - Root endpoint GET / → redirect to /docs
  Print "✓ main.py complete" when done.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Every endpoint must have a Pydantic response_model
- Every endpoint must have a try/except block raising HTTPException
- All MongoDB queries must be async (motor)
- Include OpenAPI tags for grouping in /docs
- After all steps: "PHASE 4 COMPLETE — ready for Phase 5"
```

---

---

# ═══════════════════════════════════════════════════════
# PHASE 5 — FRONTEND CORE (Layout, Shell, Components)
# ═══════════════════════════════════════════════════════

**Start a NEW Antigravity conversation. Attach NEXCART_PROMPT.md. Paste this:**

```
You are Claude Opus building NexCart. The attached NEXCART_PROMPT.md
is the full specification. The backend (Phases 1-4) is complete.

Your task in this phase is the frontend shell — the React app
structure, routing, global layout, and all shared components.
Do NOT build individual pages yet (that is Phase 6).

Design reference: Linear.app + Vercel dashboard aesthetic.
Dark theme only. Use the exact design tokens from Section 8 of the MD.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 DELIVERABLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5.1 — frontend/src/main.jsx
  React 18 root. Wrap App in QueryClientProvider (React Query).
  Configure QueryClient: staleTime=30000, retry=2.
  Print "✓ main.jsx complete" when done.

STEP 5.2 — frontend/src/api/client.js
  Axios instance with baseURL="/api" and timeout=10000.
  Add response interceptor: on 401 redirect to /login,
  on network error show a toast "Cannot reach server".
  Export typed query functions for every API endpoint:
    getStats(), getSkus(params), getSku(id), getDisruptions(),
    getNudges(params), getNudge(id), getCustomers(),
    triggerDisruptionAgent(), triggerNudgeAgent(skuIds),
    testDbConnection(), getRiskTrend(), getNudgeConversion()
  Print "✓ client.js complete" when done.

STEP 5.3 — frontend/src/App.jsx
  React Router v6 setup with these routes:
    /          → redirect to /dashboard
    /dashboard → Dashboard page
    /skus      → SKURisk page
    /signals   → Signals page
    /nudges    → Nudges page
    /analytics → Analytics page
    /settings  → Settings page
  Wrap all routes in a MainLayout component (Sidebar + TopBar).
  Print "✓ App.jsx complete" when done.

STEP 5.4 — frontend/src/components/Sidebar.jsx
  Build the full collapsible sidebar. Requirements:
  - Width: 240px expanded, 60px collapsed (icon-only)
  - Background: bg-card (#12121A), border-right: 1px solid #1E1E2E
  - NexCart logo at top (stylised text or SVG icon)
  - Navigation items with Lucide icons:
    LayoutDashboard → /dashboard
    ShieldAlert     → /skus (SKU Risk Radar)
    Radio           → /signals (Live Signals)
    Bell            → /nudges (Nudge Campaigns)
    BarChart2       → /analytics
    Settings        → /settings
  - Active item: accent-purple background pill, white text
  - Hover: bg-hover (#1A1A26)
  - Collapse toggle button at bottom of sidebar
  - On collapse: hide labels, show only icons centered
  - All transitions: 200ms ease
  Print "✓ Sidebar.jsx complete" when done.

STEP 5.5 — frontend/src/components/TopBar.jsx
  56px top bar. Requirements:
  - Background: bg-card (#12121A), bottom border: 1px solid #1E1E2E
  - Left: current page title (dynamic, passed as prop)
  - Centre: live clock (HH:MM:SS, updates every second)
  - Right side items (left to right):
    1. MongoStatus component (inline, see step 5.6)
    2. Notification bell icon with badge count
    3. Avatar circle with initials "NC" in accent-purple
  Print "✓ TopBar.jsx complete" when done.

STEP 5.6 — frontend/src/components/MongoStatus.jsx
  Live MongoDB connection indicator. Requirements:
  - Call GET /api/health/db every 30 seconds using React Query
  - Show: animated green dot + "MongoDB connected (Xms)" when ok
  - Show: animated red dot (pulsing) + "DB disconnected" on error
  - The dot must use CSS animation: pulse 1.5s ease-in-out infinite
  - Clicking the indicator navigates to /settings
  Print "✓ MongoStatus.jsx complete" when done.

STEP 5.7 — frontend/src/components/StatCard.jsx
  Reusable KPI metric card component. Props:
    label: string, value: number|string, unit?: string,
    trend?: number (% change), icon: LucideIcon, color: string
  Requirements:
  - Background: bg-card, border: 1px solid #1E1E2E, border-radius: 16px
  - Icon displayed in a small circle with colour-matched background
  - Value animates count-up from 0 on mount (use useEffect + interval)
  - Trend: green arrow up if positive, red arrow down if negative
  - Skeleton version when loading prop is true
  Print "✓ StatCard.jsx complete" when done.

STEP 5.8 — frontend/src/components/RiskBadge.jsx
  Reusable risk level pill component. Props: level: string
  Colours:
    low      → bg teal-900/30, text teal (#1D9E75), border teal-700
    medium   → bg amber-900/30, text amber (#EF9F27), border amber-700
    high     → bg orange-900/30, text orange, border orange-700
    critical → bg red-900/30, text red (#E24B4A), border red-700,
               PLUS pulsing red dot animation (animate-pulse)
  Print "✓ RiskBadge.jsx complete" when done.

STEP 5.9 — frontend/src/components/SKUTable.jsx
  Reusable paginated table for SKU data. Props:
    skus: array, loading: bool, onRowClick: fn, showPagination: bool
  Requirements:
  - Columns: SKU ID, Name, Category, Stock, Risk Score (progress bar),
    Risk Level (RiskBadge), Supplier Country, Last Updated
  - Risk score shown as a coloured progress bar (0-100)
  - Rows clickable, hover state: bg-hover
  - Skeleton rows when loading
  - Empty state: centered message with icon
  Print "✓ SKUTable.jsx complete" when done.

STEP 5.10 — frontend/src/components/DisruptionFeed.jsx
  Live feed component for disruption events/signals. Props:
    events: array, loading: bool, maxItems?: number
  Requirements:
  - Each event: source icon (newspaper/cloud/ship), title truncated,
    severity badge (1-5 stars or coloured dot), time ago string
  - Fade-in animation on new items
  - Show "No disruptions detected" with a shield icon when empty
  - Compact mode for dashboard sidebar use
  Print "✓ DisruptionFeed.jsx complete" when done.

STEP 5.11 — frontend/src/components/NudgeCard.jsx
  Card component for a single nudge campaign. Props: campaign: object
  Requirements:
  - Show: customer name, channel icon (Bell=push, Mail=email),
    at-risk SKU name → substitute SKU name (arrow between)
  - Status pill: pending=gray, sent=blue, opened=amber, converted=green
  - Show: offer text preview (max 2 lines, ellipsis)
  - Show: revenue recovered if status=converted
  - Hover: slight border highlight (accent-purple)
  Print "✓ NudgeCard.jsx complete" when done.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Tailwind classes only — no inline styles, no CSS files
- Use lucide-react for all icons
- All components must handle loading and error states
- All components must be responsive down to 768px
- After all steps: "PHASE 5 COMPLETE — ready for Phase 6"
```

---

---

# ═══════════════════════════════════════════════════════
# PHASE 6 — FRONTEND PAGES (All 6 Dashboard Views)
# ═══════════════════════════════════════════════════════

**Start a NEW Antigravity conversation. Attach NEXCART_PROMPT.md. Paste this:**

```
You are Claude Opus building NexCart. Phases 1-5 are complete.
The attached NEXCART_PROMPT.md has the full specification.

Your task is all 6 frontend pages. Build them in order.
Each page must be stunning — reference Linear.app and Vercel.
Dark theme, glass-morphism cards, smooth transitions.
Import all shared components from Phase 5 (StatCard, RiskBadge etc.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 6 DELIVERABLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 6.1 — frontend/src/pages/Dashboard.jsx
  The main command centre. Build:
  - Row 1: 4 StatCards side by side:
      "Total SKUs" (package icon, teal)
      "At Risk SKUs" (shield-alert icon, amber — count of high+critical)
      "Nudges Sent Today" (bell icon, purple)
      "Revenue Recovered (7d)" (trending-up icon, green, currency format)
  - Row 2 left (60% width): Top 5 At-Risk SKUs table using SKUTable
    component. Clicking a row → navigate to /skus/{id}
  - Row 2 right (40% width): Risk Distribution donut chart (Recharts
    PieChart). Segments: low=teal, medium=amber, high=orange,
    critical=red. Show legend below with counts.
  - Row 3 left (60%): Recent Nudge Campaigns (last 5 NudgeCards)
    with "View all" link to /nudges
  - Row 3 right (40%): Live Signal Feed (DisruptionFeed component,
    last 8 events) with SSE connection to /api/signals/feed
  - All data from React Query. Skeleton loaders during fetch.
  - Page auto-refreshes stats every 60 seconds.
  Print "✓ Dashboard.jsx complete" when done.

STEP 6.2 — frontend/src/pages/SKURisk.jsx
  Full SKU risk radar view. Build:
  - Header: "SKU Risk Radar" title + "Run Disruption Agent" button
    (triggers POST /api/agents/run-disruption, shows loading spinner)
  - Filter bar: search input, risk level dropdown (all/low/medium/
    high/critical), category dropdown, sort dropdown
  - Full paginated SKUTable with all columns visible
  - Expandable rows: clicking a row expands it to show:
    - A 7-day risk score sparkline (small Recharts LineChart)
    - List of linked disruption events
    - "Generate Nudges for this SKU" button
  - Pagination controls at the bottom
  - Stats bar above table: X total, Y at risk, Z critical
  Print "✓ SKURisk.jsx complete" when done.

STEP 6.3 — frontend/src/pages/Signals.jsx
  Live signal intelligence feed. Build:
  - Header: "Signal Intelligence" + live indicator dot (green pulsing)
    + "Ingest Manual Signal" button (opens an inline form)
  - 3 filter tabs: All | News | Weather | Shipping
  - Each signal card shows:
    - Source icon: Newspaper (news), Cloud (weather), Anchor (shipping)
    - Severity bar (1-5 filled dots)
    - Title and description (expandable)
    - Affected SKU chips (RiskBadge for each)
    - Time ago badge
  - SSE connection to GET /api/signals/feed for real-time updates
  - New signals slide in from the top with animation
  - Manual signal form (inline, not modal): fields for source,
    title, description, severity (1-5), affected_regions
  Print "✓ Signals.jsx complete" when done.

STEP 6.4 — frontend/src/pages/Nudges.jsx
  Nudge campaign management. Build:
  - Header: "Nudge Campaigns" + "Run Nudge Agent" button
  - Conversion funnel summary bar:
    [Sent: N] → [Opened: N (X%)] → [Converted: N (X%)]
    Shown as a horizontal step indicator with percentages
  - Filter bar: status tabs (All / Pending / Sent / Opened / Converted),
    channel filter (Push / Email), date range picker
  - CSS Grid of NudgeCards (2 columns on desktop, 1 on mobile)
  - Each NudgeCard has a "Mark Converted" button if status=opened
    (calls PATCH /api/nudges/{id}/status)
  - Empty state: "No campaigns yet. Run the nudge agent to start."
  Print "✓ Nudges.jsx complete" when done.

STEP 6.5 — frontend/src/pages/Analytics.jsx
  Data insights and trends. Build:
  - Header: "Analytics & Insights"
  - Row 1: 3 metric summary cards:
    "Revenue Protected (30d)", "Avg Risk Score", "Nudge Conversion Rate"
  - Row 2: Full-width line chart (Recharts LineChart) — 30-day risk
    score trend. One line per category (Electronics, Apparel, etc.)
    Each line a distinct colour. X axis: dates, Y axis: 0-100.
    Tooltip showing exact values on hover.
  - Row 3 left: Bar chart (Recharts BarChart) — nudge conversion
    by channel (Push vs Email). Grouped bars: sent, opened, converted.
  - Row 3 right: Top 5 most disrupted SKUs table (sku_name, event_count,
    avg_severity, current_risk_level)
  - Date range selector (7d / 30d / 90d) that refetches data.
  Print "✓ Analytics.jsx complete" when done.

STEP 6.6 — frontend/src/pages/Settings.jsx
  Configuration and connection management. Build:
  - Header: "Settings"
  - Section 1: "Database Connection" card
    - Input field for MONGODB_URI (masked, type=password)
    - Input field for MONGODB_DB_NAME
    - "Test Connection" button → calls GET /api/health/db
    - Result: animated status card showing green "Connected (Xms)"
      or red "Connection failed: <error>"
    - Large MongoStatus component with full details
    - Note: "Changes here update your .env file. Restart required."
  - Section 2: "External API Keys" card
    - Input fields for: NEWS_API_KEY, OPENWEATHER_API_KEY,
      MARINE_TRAFFIC_API_KEY, FIREBASE_SERVER_KEY
    - Each field has a "Test" button that calls the service
    - Show key as masked unless "Show" toggle is clicked
  - Section 3: "Agent Scheduler" card
    - Toggle: Enable/disable automatic signal polling
    - Input: Poll interval in seconds (default 300)
    - Show: "Last run: X minutes ago", "Next run in: Xm Xs"
  - Section 4: "Danger Zone" card (red border)
    - "Reseed Database" button with confirmation dialog
    - "Clear all nudge campaigns" with confirmation
  Print "✓ Settings.jsx complete" when done.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 6 RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Every page uses React Query for data fetching (useQuery)
- Every page has a proper loading skeleton (not a spinner)
- Every page has an error boundary with retry button
- Charts use Recharts only (no Chart.js)
- Currency formatted with Intl.NumberFormat("en-US", {style:"currency"})
- After all 6 pages: "PHASE 6 COMPLETE — ready for Phase 7"
```

---

---

# ═══════════════════════════════════════════════════════
# PHASE 7 — INTEGRATION, README & FINAL POLISH
# ═══════════════════════════════════════════════════════

**Start a NEW Antigravity conversation. Attach NEXCART_PROMPT.md. Paste this:**

```
You are Claude Opus. NexCart is fully built (Phases 1-6 complete).
The attached NEXCART_PROMPT.md is the full specification.

Your task in this final phase is integration verification,
the professional README, and final polish items.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 7 DELIVERABLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 7.1 — frontend/src/index.css
  Global CSS reset and base styles:
  - Import Inter from Google Fonts (@import url)
  - body: background #0A0A0F, color #E8E8F0, font-family Inter
  - Custom scrollbar: thin, dark track, purple thumb
  - CSS animation keyframes:
    @keyframes fadeSlideIn (for new signal cards)
    @keyframes countUp (for stat card numbers)
    @keyframes pulse (for MongoStatus dot and critical risk badge)
  - Tailwind base/components/utilities directives
  Print "✓ index.css complete" when done.

STEP 7.2 — frontend/src/hooks/useSSE.js
  Custom React hook for Server-Sent Events.
    useSSE(url: string) → { data, connected, error }
  - Connects to an SSE endpoint on mount
  - Parses JSON from event.data
  - Reconnects automatically after 3s on disconnect
  - Returns connected: bool for UI indicators
  - Cleanup: closes EventSource on unmount
  Print "✓ useSSE.js complete" when done.

STEP 7.3 — frontend/src/hooks/useCountUp.js
  Custom hook for count-up animation used in StatCard.
    useCountUp(target: number, duration?: number) → currentValue
  - Animates from 0 to target over duration ms (default 1200)
  - Uses requestAnimationFrame for smooth animation
  - Resets and re-animates when target changes
  Print "✓ useCountUp.js complete" when done.

STEP 7.4 — backend/tests/test_health.py
  Basic pytest tests for the health endpoints:
  - test_health_endpoint_returns_200
  - test_db_health_returns_status_field
  - test_dashboard_stats_returns_all_fields
  Use pytest-asyncio and httpx.AsyncClient.
  Print "✓ test_health.py complete" when done.

STEP 7.5 — README.md
  Write the complete professional README as specified in
  Section 11 of the attached MD. Must include:

  1. Badges row at top: Python 3.11, FastAPI, React 18,
     MongoDB, AWS Bedrock, LangGraph, Docker
  2. Project overview paragraph (2-3 sentences)
  3. ASCII architecture diagram showing:
     [News/Weather/Shipping APIs] → [Layer 1: LangGraph Agent]
     → [MongoDB] → [Layer 2: GenAI Nudge Agent]
     → [Customer Push/Email]
  4. Features list (bullet points)
  5. Prerequisites: Python 3.11+, Node 18+, Docker, MongoDB Atlas
  6. MongoDB Atlas setup (5 numbered steps with placeholders
     like: [Screenshot: Create cluster])
  7. Complete local setup walkthrough:
     Step 1: git clone ...
     Step 2: cp .env.example .env → edit with your keys
     Step 3: make install
     Step 4: make seed
     Step 5: make dev
     Step 6: open http://localhost:5173
  8. Full API endpoint table
  9. How the two agents work (plain English, 1 paragraph each)
  10. Demo walkthrough — "Simulate a disruption in 3 steps":
      Step 1: Go to Settings, confirm MongoDB connected
      Step 2: Go to Signals, click "Ingest Manual Signal",
              fill in a shipping delay with severity 5
      Step 3: Go to Dashboard, watch SKU risk scores update.
              Click "Run Nudge Agent" — check Nudges page.
  11. Academic references (McKinsey $310B, WEF supply chain,
      AWS Bedrock docs, LangGraph docs)
  12. Author / team section with placeholder fields
  Print "✓ README.md complete" when done.

STEP 7.6 — INTEGRATION CHECKLIST
  Review the full project and output a markdown checklist
  verifying all of the following are implemented:

  Backend:
  [ ] .env.example has all required variables with comments
  [ ] MongoDB connection loaded from MONGODB_URI env var only
  [ ] All 5 collections exist with correct indexes
  [ ] Layer 1 agent (disruption) runs on schedule + manual trigger
  [ ] Layer 2 agent (nudge) triggered by EventBridge + manual
  [ ] All 18 API endpoints implemented (list them)
  [ ] SSE stream endpoint at /api/signals/feed
  [ ] Seed script generates all 5 data types
  [ ] Docker-compose has all 3 services
  [ ] Graceful degradation when API keys are missing

  Frontend:
  [ ] All 6 pages built and routed
  [ ] Sidebar collapses to icon-only mode
  [ ] MongoStatus shows live connection in TopBar
  [ ] StatCards animate count-up on load
  [ ] Risk badges pulse on critical level
  [ ] Charts render on Analytics page
  [ ] Settings page has Test Connection button
  [ ] SSE connected on Signals and Dashboard pages
  [ ] All data fetches use React Query
  [ ] Responsive at 768px width

  For any item NOT implemented, describe exactly what is missing
  and how to fix it.
  Print "✓ Integration checklist complete" when done.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF ALL PHASES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
After all 6 steps, print:

"NexCart build complete.
 Total phases: 7
 To run: make dev
 Dashboard: http://localhost:5173
 API docs:  http://localhost:8000/docs"
```

---

---

## Phase Summary Table

| Phase | Scope | Key Outputs | Est. Turns |
|---|---|---|---|
| Phase 1 | Scaffold & environment | `.env.example`, `docker-compose.yml`, `package.json`, `tailwind.config.js`, `Makefile` | 1–2 |
| Phase 2 | Database layer | `connection.py`, `models.py`, `collections.py`, `config.py`, `seed.py` | 2–3 |
| Phase 3 | Services & AI agents | 5 service files, `disruption_agent.py`, `nudge_agent.py` | 3–4 |
| Phase 4 | REST API | 5 router files, `main.py` (18 endpoints total) | 2–3 |
| Phase 5 | Frontend shell | `App.jsx`, `Sidebar`, `TopBar`, `MongoStatus`, 6 shared components | 2–3 |
| Phase 6 | Frontend pages | All 6 pages: Dashboard, SKURisk, Signals, Nudges, Analytics, Settings | 3–4 |
| Phase 7 | Polish & docs | `index.css`, custom hooks, tests, `README.md`, integration checklist | 1–2 |

---

## Important Notes for Every Phase

- Always attach `NEXCART_PROMPT.md` to the conversation — it is the source of truth
- If the model asks a clarifying question, reply: "Follow the specification in the attached MD exactly"
- If any file gets cut off mid-generation, reply: "Continue from where you stopped — complete the file fully"
- After each phase, copy all generated files into your local project before starting the next phase
- Never mix two phases in one conversation — context gets confused

---

*NexCart — Final Year Project*
*AI Supply-Chain Disruption Radar + Hyper-Personalised Restock Nudging*
*Built with Claude Opus · LangGraph · AWS Bedrock · MongoDB Atlas*
