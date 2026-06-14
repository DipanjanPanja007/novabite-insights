import os
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ── DB Path ────────────────────────────────────────────────────────────────────
# main.py is imported as a module by uvicorn, so __file__ is the reliable
# anchor point — it always points to backend/main.py regardless of where
# uvicorn is invoked from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "novabite.db")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="NovaBite Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB Helper ──────────────────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with Row factory so rows behave like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.on_event("startup")
def check_db():
    if not os.path.exists(DB_PATH):
        raise RuntimeError(
            "novabite.db not found. Run 'python seed.py' first."
        )


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
    """
    Returns every distinct product with its total net revenue and
    total units sold, sorted by revenue descending.
    """
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
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        if conn:
            conn.close()


# ── Endpoint 2: Summary KPIs ───────────────────────────────────────────────────
@app.get("/api/summary")
def get_summary():
    """
    Returns 6 top-level KPIs in a single JSON object:
    total revenue, total units, gross profit margin %,
    top region, top channel, top product.
    """
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

        gross_profit_margin_pct = cursor.execute(
            "SELECT ROUND((SUM(gross_profit_usd) / NULLIF(SUM(net_revenue_usd), 0)) * 100, 2) FROM transactions"
        ).fetchone()[0]

        top_region = cursor.execute("""
            SELECT region
            FROM transactions
            GROUP BY region
            ORDER BY SUM(net_revenue_usd) DESC
            LIMIT 1
        """).fetchone()[0]

        top_channel = cursor.execute("""
            SELECT channel
            FROM transactions
            GROUP BY channel
            ORDER BY SUM(net_revenue_usd) DESC
            LIMIT 1
        """).fetchone()[0]

        top_product = cursor.execute("""
            SELECT product_name
            FROM transactions
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
    """
    Returns monthly net revenue aggregated and ordered chronologically.
    Month format is YYYY-MM so plain ASC sort works correctly.
    """
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
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        if conn:
            conn.close()