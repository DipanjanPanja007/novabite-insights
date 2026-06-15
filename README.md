# NovaBite Insights

A miniature AI-powered business intelligence chatbot built for **NovaBite Consumer Goods** — a fictional CPG company. Sales managers can explore key metrics on a dashboard and ask natural language questions about sales performance, powered by a real LLM.

Built as part of the **RevMind AI Full-Stack Take-Home Assignment (2026)**.

---

## Tech Stack

| Layer       | Technology                                         |
| ----------- | -------------------------------------------------- |
| Backend     | Python 3.14 + FastAPI                              |
| Database    | SQLite (via `sqlite3` — no external server needed) |
| LLM         | Groq API — Llama 3.3 70B Versatile                 |
| Frontend    | React 18 + Vite 5                                  |
| Styling     | Tailwind CSS v3                                    |
| Charts      | Recharts                                           |
| HTTP Client | Axios                                              |

---

## Live Demo

|             | URL         |
| ----------- | ----------- |
| Frontend    | coming soon |
| Backend API | coming soon |

---

## Project Structure

```
novabite-insights/
├── backend/
│   ├── main.py          ← FastAPI app — routes only
│   ├── database.py      ← SQLite connection + all SQL queries
│   ├── llm.py           ← Groq client + prompt builder + API call
│   ├── models.py        ← Pydantic request models
│   ├── seed.py          ← One-time CSV → SQLite seeder
│   ├── requirements.txt ← Python dependencies
│   └── novabite.db      ← Auto-generated after seeding (git-ignored)
├── frontend/
│   └── src/
│       ├── api/
│       │   └── client.js         ← Axios base instance
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── KPICard.jsx
│       │   └── RevenueChart.jsx
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   └── Chat.jsx
│       └── App.jsx
├── data/
│   └── novabite_sales_data.csv
├── .env.example
└── README.md
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A Groq API key (free at [console.groq.com](https://console.groq.com))

---

## How to Run Locally

### Step 1 — Clone the repo

```bash
git clone https://github.com/DipanjanPanja007/novabite-insights.git
cd novabite-insights
```

---

### Step 2 — Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key at [console.groq.com](https://console.groq.com) → API Keys → Create Key.

---

### Step 3 — Set up the backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed the database (run once — creates novabite.db)
python seed.py
```

Expected output:

```
Reading CSV...
Connecting to database...
Seeding transactions table...
Done! 1000 rows inserted.
```

---

### Step 4 — Start the backend server

```bash
# Still inside backend/ with venv activated
uvicorn main:app --reload
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

---

### Step 5 — Set up and start the frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

### Step 6 — Open the app

With both servers running, open your browser at:

```
http://localhost:5173
```

---

## API Endpoints

| Method | Route           | Description                                                 |
| ------ | --------------- | ----------------------------------------------------------- |
| GET    | `/api/products` | All products with total net revenue and units sold          |
| GET    | `/api/summary`  | Top-level KPIs: revenue, margin, top region/channel/product |
| GET    | `/api/trends`   | Monthly net revenue aggregated by month                     |
| POST   | `/api/chat`     | Accept `{"question": "..."}`, return `{"answer": "..."}`    |

---

## Which LLM I Used and Why

I used **Groq's Llama 3.3 70B Versatile** via the Groq inference API.

**Why Groq over Anthropic/OpenAI:**

The assignment recommended Anthropic Claude or OpenAI. However, Anthropic's API requires a credit card for account creation — which is not available to me. Groq offers a fully free tier with no credit card requirement, and critically, Groq's API is **100% OpenAI-compatible** — meaning the code structure, SDK, and request format are identical. Swapping from OpenAI to Groq required changing only two lines: the `base_url` and the model name.

Llama 3.3 70B produces high-quality, factual answers on structured data tasks — well-suited for the business intelligence use case in this assignment.

---

## How I Structured the `/api/chat` Prompt

The chat endpoint uses a **Retrieval Augmented Generation (RAG)** approach:

### Step 1 — Fetch real data from SQLite

Before calling the LLM, the endpoint runs 10 targeted SQL queries:

- Overall summary (total revenue, units, margin)
- Revenue by region (all time)
- Revenue by channel (all time)
- Revenue + margin by category
- Top 10 products by revenue
- Top 10 sales reps by units
- Q1 2024 revenue by region ← specifically for test question 1
- 2025 revenue by channel ← for test question 4
- Top 5 products in West region ← for test question 5
- Top 5 sales reps in 2025 ← for test question 3

### Step 2 — Build a system prompt with the data embedded

```
You are a senior business analyst for NovaBite Consumer Goods.
Answer questions using ONLY the data provided below.

OVERALL SUMMARY:
  Total Net Revenue: $1,285,746.13
  Gross Profit Margin: 52.42%

REVENUE BY REGION:
  - region: West | revenue: 284521.45
  ...

Q1-2024 REVENUE BY REGION:
  - region: South | revenue: 37640.11
  ...

Answer the following question:
```

### Step 3 — Send to Groq

The prompt goes as the `system` message. The user's question goes as the `user` message. Llama 3.3 reads the embedded data and answers accurately — it never hallucinates because all answers come from the data we provide.

**Why this approach works:** The model doesn't need to "know" NovaBite's data from training. We inject the exact numbers it needs on every request. This is standard practice in production LLM applications.

---

## What I Would Improve With More Time

1. **Streaming responses** — Stream the LLM output token-by-token for a typewriter effect in the UI. Groq supports streaming via the same SDK.

2. **Dynamic SQL generation** — Instead of pre-running 10 fixed queries, use the LLM to generate SQL from the user's question, run it, and answer from live results. More flexible for questions outside the pre-defined scope.

3. **Unit tests** — At minimum, tests for `fetch_summary()` and `build_prompt()` to verify SQL correctness and prompt structure.

4. **Docker Compose** — A `docker-compose.yml` to run both backend and frontend with a single command, eliminating the manual setup steps.

5. **Second chart** — A bar chart showing revenue by category or region breakdown on the dashboard.

6. **Environment-based CORS** — Currently CORS is hardcoded to `localhost:5173`. In production this should read from an environment variable.

---

## Tradeoffs and Shortcuts

| Decision                         | Reason                                                                                                    |
| -------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Groq instead of Anthropic/OpenAI | No credit card available for Anthropic/OpenAI free tier signup                                            |
| SQLite instead of PostgreSQL     | Assignment explicitly allows it; simpler setup, no external server                                        |
| Pre-fetching fixed SQL queries   | Ensures 100% accuracy on the 5 required test questions; tradeoff is inflexibility for edge-case questions |
| No authentication                | Out of scope for this assignment; a real product would require JWT or session auth                        |
| No query caching                 | Each `/api/chat` call re-runs all 10 SQL queries; acceptable for 1000 rows, would need caching at scale   |

---

## Example Questions the Chat Answers

1. "Which region had the highest net revenue in Q1 2024?"
2. "What is the gross profit margin for the Snacks category?"
3. "Which sales rep closed the most units in 2025?"
4. "Compare E-Commerce vs Modern Trade net revenue."
5. "What was the best performing product in the West region?"
