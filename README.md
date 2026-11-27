# NexCart

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)
![React 18](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq-000000)
![Gemini](https://img.shields.io/badge/LLM-Gemini-4285F4)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-7C6DDD)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

> **Predict shelf gaps before they happen. Recover demand through personalised offers.**

NexCart is an AI-powered supply-chain disruption radar that monitors real-time signals from news, weather, and shipping sources, predicts which SKUs are at risk using a LangGraph agent with Groq/Gemini, and automatically generates hyper-personalised restock nudges to affected customers — recovering lost revenue before it happens.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SIGNAL SOURCES                      │
│   ┌──────────┐    ┌──────────────┐    ┌─────────────────┐          │
│   │ NewsAPI   │    │ OpenWeather  │    │ MarineTraffic   │          │
│   └─────┬────┘    └──────┬───────┘    └────────┬────────┘          │
│         └────────────────┼─────────────────────┘                    │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │         LAYER 1: LangGraph Disruption Prediction Agent       │   │
│  │  ingest_signals → analyse_risk → update_sku_scores           │   │
│  │  → flag_at_risk_skus → publish_to_eventbridge                │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             ▼                                       │
│                    ┌────────────────┐                                │
│                    │  MongoDB Atlas │                                │
│                    │   5 Collections│                                │
│                    └───────┬────────┘                                │
│                            ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │       LAYER 2: LangGraph GenAI Personalisation Agent         │   │
│  │  load_at_risk_customers → find_substitutes                   │   │
│  │  → generate_offer_copy → dispatch_nudges → log_campaign      │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             ▼                                       │
│               ┌─────────────────────────┐                           │
│               │   Customer Channels     │                           │
│               │  📱 Push  │  📧 Email   │                           │
│               └─────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Features

- 🔍 **Real-Time Signal Monitoring** — Ingests disruption signals from news, weather, and shipping APIs
- 🤖 **AI Risk Prediction** — LangGraph agent routes structured analysis requests across Groq and Gemini
- 📊 **Risk Scoring** — Composite risk scores (0-100) with automatic risk level classification
- 💬 **GenAI Personalisation** — Generates warm, personalised customer messages with substitute product recommendations
- 📱 **Multi-Channel Nudges** — Push notifications (FCM) and email campaigns with conversion tracking
- 📈 **Analytics Dashboard** — Risk trends, conversion funnels, and revenue recovery metrics
- 🔴 **Live Signal Feed** — Server-Sent Events (SSE) for real-time updates
- ⚡ **Auto-Scheduling** — APScheduler runs disruption detection at configurable intervals
- 🐳 **Docker Ready** — Full docker-compose setup with MongoDB, backend, and frontend

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker | Latest |
| MongoDB Atlas | Free tier (M0) or local MongoDB |

---

## MongoDB Atlas Setup

1. **Create an Account** — Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) and sign up for a free account.
   
   *[Screenshot: Create Atlas account]*

2. **Create a Free Cluster** — Click "Build a Database" → select **M0 Free Tier** → choose your cloud provider and region.
   
   *[Screenshot: Create cluster]*

3. **Create a Database User** — Go to **Database Access** → Add New Database User → set username and password.
   
   *[Screenshot: Create database user]*

4. **Allow Your App's IP** — Go to **Network Access** → Add IP Address → add your current public IP for local development, or your deployment server's fixed egress IP. Avoid leaving access open to everyone.
   
   *[Screenshot: Network access]*

5. **Get Your Connection String** — Click **Connect** on your cluster → "Connect your application" → copy the URI.
   
   *[Screenshot: Connection string]*

Replace `<password>` with your database user's password (URL-encode special characters). Put the completed URI in `.env` as `MONGODB_URI=...` and set `MONGODB_DB_NAME=nexcart`. Keep `.env` private and out of Git.

### Move existing local data to Atlas

Install MongoDB Database Tools, then stop the backend briefly to avoid writes during the copy. The Docker Compose local database is exposed on `localhost:27017`.

```powershell
docker compose stop nexcart-backend
mongodump --uri="mongodb://localhost:27017/nexcart" --out=".\mongo-backup"
mongorestore --uri="<Atlas URI ending in /nexcart>" --nsInclude="nexcart.*" ".\mongo-backup\nexcart"
```

Restore into a new, empty Atlas database. In `docker-compose.yml`, the backend uses `MONGODB_URI` from `.env` when set and otherwise defaults to the local MongoDB container. Recreate the backend after setting the Atlas URI:

```powershell
docker compose up -d --force-recreate nexcart-backend
```

Check `http://localhost:8000/api/health/db` and verify the collections and document counts in Atlas Data Explorer before deleting or changing the local database volume. The local volume is kept as a rollback copy.

---

## Local Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/nexcart.git
cd nexcart
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:
- **MONGODB_URI** — Your Atlas connection string (required)
- **GROQ_API_KEY** and **GEMINI_API_KEY** — Optional LLM providers; either or both can be configured. Failed or unavailable providers fall back to heuristic scoring and local message templates.
- **AWS credentials** — Optional for EventBridge only; not required for LLM features
- **API keys** — For NewsAPI, OpenWeatherMap, MarineTraffic (optional, uses mock data)

### Step 3: Install Dependencies

Run the one-click setup script for your platform:

```powershell
.\setup.bat
```

```bash
sh ./setup.sh
```

The script checks for Python 3.11+, Node.js 18+, and npm; installs backend packages into `.venv`; installs frontend packages from the lockfile; and creates `.env` from `.env.example` if needed. Fill in the required credentials in `.env` before starting the app.

Alternatively, install dependencies manually:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
npm --prefix frontend ci
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

### Step 4: Seed the Database

```bash
make seed
```

This generates:
- 50 SKUs across 5 categories
- 200 customer profiles with purchase histories
- 20 disruption events
- 100 nudge campaigns
- 500 signal log entries

### Step 5: Start Development Servers

```bash
make dev
```

Or with Docker:
```bash
docker-compose up
```

### Step 6: Open the App

- **Dashboard:** [http://localhost:5173](http://localhost:5173)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | App status + version |
| GET | `/api/health/db` | MongoDB ping + latency |
| GET | `/api/dashboard/stats` | KPI summary stats |
| GET | `/api/skus` | Paginated SKU list (risk sorted) |
| GET | `/api/skus/{sku_id}` | Single SKU + risk history |
| POST | `/api/skus` | Create new SKU |
| PATCH | `/api/skus/{sku_id}/risk` | Override risk level |
| GET | `/api/disruptions` | Recent disruption events |
| GET | `/api/disruptions/{id}` | Single disruption event |
| GET | `/api/signals/feed` | Live signal stream (SSE) |
| POST | `/api/signals/ingest` | Manual signal submission |
| GET | `/api/signals/history` | Signal log history |
| GET | `/api/nudges` | All nudge campaigns |
| GET | `/api/nudges/{id}` | Single campaign detail |
| PATCH | `/api/nudges/{id}/status` | Update campaign status |
| GET | `/api/analytics/risk-trend` | 30-day risk time series |
| GET | `/api/analytics/nudge-conversion` | Conversion funnel stats |
| POST | `/api/agents/run-disruption` | Trigger Layer 1 agent |
| POST | `/api/agents/run-nudge` | Trigger Layer 2 agent |
| GET | `/api/customers` | Customer profiles |
| POST | `/api/customers` | Create customer |

---

## How the Agents Work

### Layer 1: Disruption Prediction Agent

The disruption agent runs on a configurable schedule (default: every 5 minutes). It pulls real-time signals from news, weather, and shipping APIs, then tries Groq and Gemini in a rotating order to identify affected SKUs and generate structured reasoning. If both providers fail or are unavailable, it falls back to the heuristic risk scorer using stock-to-reorder-point ratios and signal severity weights. High-risk SKUs are flagged via Amazon EventBridge, which triggers Layer 2.

### Layer 2: GenAI Personalisation Agent

When triggered by a disruption event, this agent identifies customers who recently purchased at-risk products, finds safe substitute SKUs in the same category, and requests generic copy from Groq or Gemini. Identical LLM requests are cached for five minutes, and copy is reused for customers with the same product/substitute pair, then personalized locally; customer names, email addresses, and purchase histories are not sent to LLM providers. If both providers fail, a local message template is used. Messages are dispatched via push notification or email based on the customer's profile, and campaign outcomes (sent → opened → converted) are tracked for analytics.

---

## Demo Walkthrough — Simulate a Disruption in 3 Steps

### Step 1: Verify Connection
Go to **Settings** → confirm the MongoDB status shows a green "Connected" indicator with latency.

### Step 2: Ingest a Manual Signal
Navigate to **Signals** → click "Ingest Manual Signal" → fill in:
- **Source:** Shipping
- **Title:** "Port strike at Shanghai delays semiconductor shipments"
- **Severity:** 5 (Critical)
- **Regions:** Shanghai, East Asia

Click **Submit Signal** and watch it appear in the live feed.

### Step 3: Watch the Agents Respond
Go to **Dashboard** → observe SKU risk scores updating in real-time. Click **"Run Disruption Agent"** on the SKU Risk Radar page to force an immediate analysis. Then navigate to **Nudges** → click **"Run Nudge Agent"** to generate personalised customer campaigns. Check the conversion funnel to see campaign delivery stats.

---

## Role-Based Workspaces

NexCart provides three role-specific experiences. Each account is routed to its own landing page after authentication:

| Role | Workspace | Landing page | Focus |
|------|-----------|--------------|-------|
| `admin` | Governance | `/admin/dashboard` | User administration, access grants, audit history, platform health, activity, and settings |
| `manager` | Operations | `/manager/dashboard` | Inventory priorities, SKU management, disruptions, signal monitoring, and operational analytics |
| `viewer` | Intelligence | `/intelligence/overview` | Read-only risk, disruption, signal, and analytics exploration |

Use the development demo-account buttons on the login screen to fill in the available test accounts. Demo accounts are only provisioned when `APP_ENV` is not `production`. Backend permissions remain authoritative; navigating directly to a restricted workspace is denied.

## Academic References

1. **McKinsey & Company** (2020). *"Risk, resilience, and rebalancing in global value chains."* — Supply chain disruptions cost global companies $310 billion annually.

2. **World Economic Forum** (2023). *"Global Risks Report 2023."* — Supply chain instability ranked among the top 10 global risks for 5 consecutive years.

3. **Groq Documentation**. *"Groq API — Fast inference for LLM applications."* [https://console.groq.com/docs/](https://console.groq.com/docs/)

4. **Google Gemini API**. *"Gemini Developer API documentation."* [https://ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)

5. **LangGraph Documentation**. *"Build stateful, multi-actor applications with LLMs."* [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/)

6. **MongoDB Atlas**. *"Developer Data Platform."* [https://www.mongodb.com/atlas](https://www.mongodb.com/atlas)

7. **Chopra, S. & Meindl, P.** (2016). *Supply Chain Management: Strategy, Planning, and Operation.* 6th Edition, Pearson.

---

## Team

| Role | Name |
|------|------|
| Developer | *[Your Name]* |
| University | *[Your University]* |
| Programme | *[B.Tech / M.Tech]* |
| Year | Final Year (2025-26) |
| Hackathon | Cognizant AI Hackathon |

---

## Tech Stack Summary

```
Backend:   Python 3.11 · FastAPI · Motor (async MongoDB) · LangGraph · LangChain
AI:        Groq · Gemini · Heuristic Risk Scoring · GenAI Personalisation
Database:  MongoDB Atlas · 5 Collections · Async Indexes
Frontend:  React 18 · Vite · TailwindCSS · Recharts · React Query · Lucide Icons
Infra:     Docker Compose · APScheduler · Amazon EventBridge
Channels:  Firebase Cloud Messaging (Push) · SMTP (Email)
```

---

*NexCart — Final Year Project | AI Supply-Chain Disruption Radar*
*Built with Groq · Gemini · LangGraph · MongoDB Atlas*
