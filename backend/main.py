import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import DB_PATH, fetch_products, fetch_summary, fetch_trends, fetch_chat_context
from models import ChatRequest
from llm import ask_groq

# ── Environment ────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(_BASE_DIR, "..", ".env"))


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Abort startup if the database has not been seeded yet."""
    if not os.path.exists(DB_PATH):
        raise RuntimeError(
            "novabite.db not found. Run 'python seed.py' first."
        )
    yield


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="NovaBite Insights API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "NovaBite API running",
        "version": "1.0.0",
        "docs":    "/docs",
    }


@app.get("/api/products")
def get_products():
    try:
        return fetch_products()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/summary")
def get_summary():
    try:
        return fetch_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/trends")
def get_trends():
    try:
        return fetch_trends()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/chat")
def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        ctx = fetch_chat_context()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    try:
        answer = ask_groq(request.question.strip(), ctx)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")

    return {"answer": answer}