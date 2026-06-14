import os
import sqlite3

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "novabite.db")


# ── Connection Helper ──────────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection whose rows behave like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Query: Products ────────────────────────────────────────────────────────────
def fetch_products() -> list:
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
    finally:
        if conn:
            conn.close()


# ── Query: Summary KPIs ────────────────────────────────────────────────────────
def fetch_summary() -> dict:
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
    finally:
        if conn:
            conn.close()


# ── Query: Monthly Trends ──────────────────────────────────────────────────────
def fetch_trends() -> list:
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
    finally:
        if conn:
            conn.close()


# ── Query: Chat Context (all 10 queries for LLM prompt) ───────────────────────
def fetch_chat_context() -> dict:
    """
    Runs all 10 analytical queries needed to build the LLM prompt.
    Returns a single dict with all results.
    """
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

        return {
            "summary":        summary,
            "regions":        regions,
            "channels":       channels,
            "categories":     categories,
            "top_products":   top_products,
            "top_reps":       top_reps,
            "q1_2024_regions": q1_2024_regions,
            "channels_2025":  channels_2025,
            "west_products":  west_products,
            "reps_2025":      reps_2025,
        }
    finally:
        if conn:
            conn.close()