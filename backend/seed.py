import os
import sqlite3
import pandas as pd



# ── Paths ──────────────────────────────────────────────────────────────────────
# Run this script from inside the backend/ folder: python seed.py
# os.getcwd() will resolve to backend/, so paths stay portable across OS.
BASE_DIR = os.getcwd()
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "novabite_sales_data.csv")
DB_PATH  = os.path.join(BASE_DIR, "novabite.db")

# ── SQL ────────────────────────────────────────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE transactions (
    transaction_id     TEXT PRIMARY KEY,
    date               TEXT,
    month              TEXT,
    quarter            TEXT,
    sku                TEXT,
    product_name       TEXT,
    category           TEXT,
    subcategory        TEXT,
    region             TEXT,
    channel            TEXT,
    sales_rep          TEXT,
    units_sold         INTEGER,
    unit_price_usd     REAL,
    gross_revenue_usd  REAL,
    discount_pct       REAL,
    net_revenue_usd    REAL,
    cogs_usd           REAL,
    gross_profit_usd   REAL
);
"""

INSERT_SQL = """
INSERT INTO transactions (
    transaction_id, date, month, quarter, sku, product_name,
    category, subcategory, region, channel, sales_rep,
    units_sold, unit_price_usd, gross_revenue_usd, discount_pct,
    net_revenue_usd, cogs_usd, gross_profit_usd
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    # 1. Read CSV
    print("Reading CSV...")
    df = pd.read_csv(CSV_PATH)

    # 2. Connect to SQLite (creates novabite.db if it doesn't exist)
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 3. Drop existing table so re-runs don't duplicate data
    print("Seeding transactions table...")
    cursor.execute("DROP TABLE IF EXISTS transactions;")
    cursor.execute(CREATE_TABLE_SQL)

    # 4. Build rows with explicit type casting for safety
    rows = [
        (
            str(row.transaction_id),
            str(row.date),
            str(row.month),
            str(row.quarter),
            str(row.sku),
            str(row.product_name),
            str(row.category),
            str(row.subcategory),
            str(row.region),
            str(row.channel),
            str(row.sales_rep),
            int(row.units_sold),
            float(row.unit_price_usd),
            float(row.gross_revenue_usd),
            float(row.discount_pct),
            float(row.net_revenue_usd),
            float(row.cogs_usd),
            float(row.gross_profit_usd),
        )
        for row in df.itertuples(index=False)
    ]

    # 5. Bulk insert all rows in one call
    cursor.executemany(INSERT_SQL, rows)
    conn.commit()

    # 6. Verify row count and close cleanly
    count = cursor.execute("SELECT COUNT(*) FROM transactions;").fetchone()[0]
    conn.close()

    print(f"Done! {count} rows inserted.")

if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print("ERROR: CSV file not found. Check that data/novabite_sales_data.csv exists.")
    except Exception as e:
        print(f"ERROR: {e}")

