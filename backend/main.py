import os
import sqlite3
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

# ── Paths ──────────────────────────────────────────────────────────────────────
# __file__ always points to backend/main.py regardless of where uvicorn starts.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "novabite.db")

# ── Environment ────────────────────────────────────────────────────────────────
# .env lives in project root (one level above backend/).
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "..", ".env"))

# ── Gemini Client (initialised once at module level) ──────────────────────────
# Line 1 — client:
gemini_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

# Line 2 — model:
# model="gemini-1.5-flash"
model="llama-3.3-70b-versatile",

# ── Lifespan (startup check — modern FastAPI pattern) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once on startup. Aborts if the database has not been seeded yet."""
    if not os.path.exists(DB_PATH):
        raise RuntimeError(
            "novabite.db not found. Run 'python seed.py' first."
        )
    yield   # app runs here; anything after yield runs on shutdown


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="NovaBite Insights API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB Helper ──────────────────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection whose rows behave like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Prompt Helper (module-level, not re-created per request) ──────────────────
def fmt_list(rows: list, *keys: str) -> str:
    """Format a list of dicts into clean bullet lines for the LLM prompt."""
    return "\n".join(
        "  - " + " | ".join(f"{k}: {row[k]}" for k in keys)
        for row in rows
    )


# ── Pydantic Models ────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "NovaBite API running",
        "version": "1.0.0",
        "docs":    "/docs",
    }


# ── Endpoint 1: Products ───────────────────────────────────────────────────────
@app.get("/api/products")
def get_products():
    """Every distinct product with total net revenue and units, by revenue desc."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                product_name,
                ROUND(SUM(net_revenue_usd), 2) AS total_net_revenue,
                SUM(units_sold)                AS total_units_sold
            FROM transactions
            GROUP BY product_name
            ORDER BY total_net_revenue DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        if conn:
            conn.close()


# ── Endpoint 2: Summary KPIs ───────────────────────────────────────────────────
@app.get("/api/summary")
def get_summary():
    """Six top-level KPIs: revenue, units, margin, top region/channel/product."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        total_net_revenue = cursor.execute(
            "SELECT ROUND(SUM(net_revenue_usd), 2) FROM transactions"
        ).fetchone()[0]

        total_units_sold = cursor.execute(
            "SELECT SUM(units_sold) FROM transactions"
        ).fetchone()[0]

        gross_profit_margin_pct = cursor.execute("""
            SELECT ROUND(
                (SUM(gross_profit_usd) / NULLIF(SUM(net_revenue_usd), 0)) * 100,
            2) FROM transactions
        """).fetchone()[0]

        top_region = cursor.execute("""
            SELECT region FROM transactions
            GROUP BY region
            ORDER BY SUM(net_revenue_usd) DESC
            LIMIT 1
        """).fetchone()[0]

        top_channel = cursor.execute("""
            SELECT channel FROM transactions
            GROUP BY channel
            ORDER BY SUM(net_revenue_usd) DESC
            LIMIT 1
        """).fetchone()[0]

        top_product = cursor.execute("""
            SELECT product_name FROM transactions
            GROUP BY product_name
            ORDER BY SUM(net_revenue_usd) DESC
            LIMIT 1
        """).fetchone()[0]

        return {
            "total_net_revenue":       total_net_revenue,
            "total_units_sold":        total_units_sold,
            "gross_profit_margin_pct": gross_profit_margin_pct,
            "top_region":              top_region,
            "top_channel":             top_channel,
            "top_product":             top_product,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        if conn:
            conn.close()


# ── Endpoint 3: Monthly Trends ─────────────────────────────────────────────────
@app.get("/api/trends")
def get_trends():
    """Monthly net revenue aggregated and ordered chronologically (YYYY-MM)."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                month,
                ROUND(SUM(net_revenue_usd), 2) AS total_net_revenue
            FROM transactions
            GROUP BY month
            ORDER BY month ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        if conn:
            conn.close()


# ── Endpoint 4: Chat ───────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Accepts a natural-language question, enriches a prompt with live SQLite
    data, calls Gemini, and returns the answer.
    """

    # STEP 1 — Validate input
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # STEP 2 — Fetch all context data from DB
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # A: Overall summary
        summary = dict(cursor.execute("""
            SELECT
                ROUND(SUM(net_revenue_usd), 2)                                             AS total_revenue,
                SUM(units_sold)                                                            AS total_units,
                ROUND((SUM(gross_profit_usd) / NULLIF(SUM(net_revenue_usd), 0)) * 100, 2) AS margin_pct
            FROM transactions
        """).fetchone())

        # B: Revenue by region (all time)
        regions = [dict(r) for r in cursor.execute("""
            SELECT region, ROUND(SUM(net_revenue_usd), 2) AS revenue
            FROM transactions
            GROUP BY region
            ORDER BY revenue DESC
        """).fetchall()]

        # C: Revenue by channel (all time)
        channels = [dict(r) for r in cursor.execute("""
            SELECT channel, ROUND(SUM(net_revenue_usd), 2) AS revenue
            FROM transactions
            GROUP BY channel
            ORDER BY revenue DESC
        """).fetchall()]

        # D: Revenue + margin by category
        categories = [dict(r) for r in cursor.execute("""
            SELECT
                category,
                ROUND(SUM(net_revenue_usd), 2)                                             AS revenue,
                ROUND((SUM(gross_profit_usd) / NULLIF(SUM(net_revenue_usd), 0)) * 100, 2) AS margin_pct
            FROM transactions
            GROUP BY category
            ORDER BY revenue DESC
        """).fetchall()]

        # E: Top 10 products by revenue
        top_products = [dict(r) for r in cursor.execute("""
            SELECT product_name, ROUND(SUM(net_revenue_usd), 2) AS revenue
            FROM transactions
            GROUP BY product_name
            ORDER BY revenue DESC
            LIMIT 10
        """).fetchall()]

        # F: Top 10 sales reps by units (all time)
        top_reps = [dict(r) for r in cursor.execute("""
            SELECT sales_rep, SUM(units_sold) AS total_units
            FROM transactions
            GROUP BY sales_rep
            ORDER BY total_units DESC
            LIMIT 10
        """).fetchall()]

        # G: Revenue by region — Q1 2024
        q1_2024_regions = [dict(r) for r in cursor.execute("""
            SELECT region, ROUND(SUM(net_revenue_usd), 2) AS revenue
            FROM transactions
            WHERE quarter = 'Q1-2024'
            GROUP BY region
            ORDER BY revenue DESC
        """).fetchall()]

        # H: Revenue by channel — 2025 only
        channels_2025 = [dict(r) for r in cursor.execute("""
            SELECT channel, ROUND(SUM(net_revenue_usd), 2) AS revenue
            FROM transactions
            WHERE date LIKE '2025%'
            GROUP BY channel
            ORDER BY revenue DESC
        """).fetchall()]

        # I: Top 5 products in West region
        west_products = [dict(r) for r in cursor.execute("""
            SELECT product_name, ROUND(SUM(net_revenue_usd), 2) AS revenue
            FROM transactions
            WHERE region = 'West'
            GROUP BY product_name
            ORDER BY revenue DESC
            LIMIT 5
        """).fetchall()]

        # J: Top 5 sales reps in 2025 by units
        reps_2025 = [dict(r) for r in cursor.execute("""
            SELECT sales_rep, SUM(units_sold) AS total_units
            FROM transactions
            WHERE date LIKE '2025%'
            GROUP BY sales_rep
            ORDER BY total_units DESC
            LIMIT 5
        """).fetchall()]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        if conn:
            conn.close()

    # STEP 3 — Build prompt with all data embedded
    system_prompt = f"""You are a senior business analyst for NovaBite Consumer Goods, a CPG company.
You have access to the complete sales database for Jan 2024 - Dec 2025.
Answer questions accurately using ONLY the data provided below.
Be concise, factual, and specific. Always include actual numbers in your answer.

=== NOVABITE SALES DATA ===

OVERALL SUMMARY:
  Total Net Revenue : ${summary['total_revenue']}
  Total Units Sold  : {summary['total_units']}
  Gross Profit Margin: {summary['margin_pct']}%

REVENUE BY REGION (ALL TIME):
{fmt_list(regions, 'region', 'revenue')}

REVENUE BY CHANNEL (ALL TIME):
{fmt_list(channels, 'channel', 'revenue')}

REVENUE BY CATEGORY (with gross profit margin %):
{fmt_list(categories, 'category', 'revenue', 'margin_pct')}

TOP 10 PRODUCTS BY REVENUE:
{fmt_list(top_products, 'product_name', 'revenue')}

TOP 10 SALES REPS BY UNITS (ALL TIME):
{fmt_list(top_reps, 'sales_rep', 'total_units')}

Q1-2024 REVENUE BY REGION:
{fmt_list(q1_2024_regions, 'region', 'revenue')}

2025 REVENUE BY CHANNEL:
{fmt_list(channels_2025, 'channel', 'revenue')}

TOP 5 PRODUCTS IN WEST REGION:
{fmt_list(west_products, 'product_name', 'revenue')}

TOP 5 SALES REPS IN 2025 (BY UNITS):
{fmt_list(reps_2025, 'sales_rep', 'total_units')}

=== END OF DATA ===

Answer the following question based strictly on the data above:"""

    # STEP 4 — Call Gemini
    try:
        response = gemini_client.chat.completions.create(
            model="llama-3.3-70b-versatile",

            max_tokens=1000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": request.question.strip()},
            ],
        )
        answer = response.choices[0].message.content

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")

    # STEP 5 — Return answer
    return {"answer": answer}