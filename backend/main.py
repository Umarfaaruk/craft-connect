"""
Craft Connect — FastAPI Backend
================================

This is the main entry point for the Craft Connect backend server.
It exposes a REST API that acts as a **proxy** between the Streamlit
frontend and the external Swecha Corpus API.

Architecture:
    ┌──────────────┐      ┌──────────────────┐      ┌────────────────────────┐
    │  Streamlit   │ ──── │  This FastAPI     │ ──── │  Swecha Corpus API     │
    │  Frontend    │ HTTP │  Backend (proxy)  │ HTTP │  api.corpus.swecha.org │
    └──────────────┘      └──────────────────┘      └────────────────────────┘

Endpoints:
    POST /token           — Login and receive an access token
    POST /auth/register   — Register a new user account
    GET  /crafts          — List all public craft records
    POST /crafts          — Upload a new craft (requires auth)
    GET  /categories      — List available craft categories

Running:
    cd backend
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""

# ──────────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────────
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from services import corpus_service     # All Corpus API logic lives here

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()                           # Load .env file (SWECHA_API_BASE_URL, etc.)

app = FastAPI(
    title="Craft Connect API",
    description="Proxy API for the Swecha Corpus platform — preserving traditional crafts & cultural heritage.",
    version="1.0.0",
)

# ──────────────────────────────────────────────────────────────────────────────
# Security
# ──────────────────────────────────────────────────────────────────────────────
# OAuth2 password flow — the frontend sends credentials to /token
# and receives a bearer token for subsequent requests.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ──────────────────────────────────────────────────────────────────────────────
# CORS Middleware
# ──────────────────────────────────────────────────────────────────────────────
# Allow all origins during development.
# For production: replace "*" with the actual frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,               # Cache preflight responses for 1 hour
)


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    """Standard OAuth2 token response."""
    access_token: str
    token_type: str


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS — Authentication
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    **Login** — Authenticate with phone number and password.

    Proxies the credentials to the Corpus API login endpoint and
    returns a bearer access token on success.
    """
    return await corpus_service.login_for_token(form_data.username, form_data.password)


@app.post("/auth/register", response_model=Token, tags=["Authentication"])
async def register(
    username: str = Form(..., description="Phone number"),
    password: str = Form(..., description="Account password"),
    email: str = Form(None, description="Optional email address"),
):
    """
    **Register** — Create a new user account.

    Calls the Corpus API registration endpoint. If successful,
    returns a bearer access token so the user is immediately logged in.
    """
    return await corpus_service.register_user(username, password, email)


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS — Crafts
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/crafts", tags=["Crafts"])
async def get_all_crafts():
    """
    **List Crafts** — Fetch all public craft records.

    Returns a JSON array of craft objects from the Corpus API.
    If the API is unavailable or requires auth, returns an empty list.
    """
    return await corpus_service.get_all_crafts_from_corpus()


@app.post("/crafts", tags=["Crafts"])
async def upload_craft(
    token: Annotated[str, Depends(oauth2_scheme)],
    description: Annotated[str, Form(description="Craft description (used as title too)")],
    category_id: Annotated[str, Form(description="Category ID from /categories")],
    language: Annotated[str, Form(description="Language code or 'NA'")],
    release_rights: Annotated[str, Form(description="'creator', 'others', 'downloaded', or 'NA'")],
    file: Annotated[UploadFile, File(description="Image or video file (max 1 GB)")],
):
    """
    **Upload Craft** — Publish a new craft to the gallery.

    Requires a valid bearer token. The file and metadata are forwarded
    to the Corpus API's upload endpoint.
    """
    return await corpus_service.upload_craft_to_corpus(
        token=token,
        description=description,
        file=file,
        category_id=category_id,
        language=language,
        release_rights=release_rights,
    )


@app.get("/categories", tags=["Crafts"])
async def categories():
    """
    **List Categories** — Fetch available craft categories.

    Returns a JSON array of category objects (each with ``id`` and ``name``).
    """
    return await corpus_service.get_categories_from_corpus()