import os
from dotenv import load_dotenv
from openai import OpenAI

# ── Environment ────────────────────────────────────────────────────────────────
# Load .env explicitly so this module works correctly when imported.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(_BASE_DIR, "..", ".env"))

# ── Groq Client (initialised once at module level) ────────────────────────────
_groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

# ── Model ─────────────────────────────────────────────────────────────────────
_MODEL = "llama-3.3-70b-versatile"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fmt_list(rows: list, *keys: str) -> str:
    """Format a list of dicts into clean bullet lines for the LLM prompt."""
    return "\n".join(
        "  - " + " | ".join(f"{k}: {row[k]}" for k in keys)
        for row in rows
    )


# ── Prompt Builder ────────────────────────────────────────────────────────────
def build_prompt(ctx: dict) -> str:
    """
    Takes the dict returned by fetch_chat_context() and returns
    a fully formatted system prompt with all data embedded.
    """
    return f"""You are a senior business analyst for NovaBite Consumer Goods, a CPG company.
You have access to the complete sales database for Jan 2024 - Dec 2025.
Answer questions accurately using ONLY the data provided below.
Be concise, factual, and specific. Always include actual numbers in your answer.

=== NOVABITE SALES DATA ===

OVERALL SUMMARY:
  Total Net Revenue : ${ctx['summary']['total_revenue']}
  Total Units Sold  : {ctx['summary']['total_units']}
  Gross Profit Margin: {ctx['summary']['margin_pct']}%

REVENUE BY REGION (ALL TIME):
{_fmt_list(ctx['regions'], 'region', 'revenue')}

REVENUE BY CHANNEL (ALL TIME):
{_fmt_list(ctx['channels'], 'channel', 'revenue')}

REVENUE BY CATEGORY (with gross profit margin %):
{_fmt_list(ctx['categories'], 'category', 'revenue', 'margin_pct')}

TOP 10 PRODUCTS BY REVENUE:
{_fmt_list(ctx['top_products'], 'product_name', 'revenue')}

TOP 10 SALES REPS BY UNITS (ALL TIME):
{_fmt_list(ctx['top_reps'], 'sales_rep', 'total_units')}

Q1-2024 REVENUE BY REGION:
{_fmt_list(ctx['q1_2024_regions'], 'region', 'revenue')}

2025 REVENUE BY CHANNEL:
{_fmt_list(ctx['channels_2025'], 'channel', 'revenue')}

TOP 5 PRODUCTS IN WEST REGION:
{_fmt_list(ctx['west_products'], 'product_name', 'revenue')}

TOP 5 SALES REPS IN 2025 (BY UNITS):
{_fmt_list(ctx['reps_2025'], 'sales_rep', 'total_units')}

=== END OF DATA ===

Answer the following question based strictly on the data above:"""


# ── Public API ────────────────────────────────────────────────────────────────
def ask_groq(question: str, ctx: dict) -> str:
    """
    Builds the prompt from ctx, calls Groq, and returns the answer string.
    Raises an exception on API failure (caller handles HTTP error codes).
    """
    system_prompt = build_prompt(ctx)
    response = _groq_client.chat.completions.create(
        model=_MODEL,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": question},
        ],
    )
    return response.choices[0].message.content