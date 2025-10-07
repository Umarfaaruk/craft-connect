# backend/main.py

import os
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from services import corpus_service

# --- 1. Configuration ---
load_dotenv()

# --- 2. Create the FastAPI App Instance ---
app = FastAPI(title="Craft Connect API")

# --- 3. Security Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- 4. CORS Middleware ---
# Define the list of allowed origins (your frontend URLs)
# For local testing, you can add "http://localhost:8501"
origins = [
    "https://craft-connect.streamlit.app/", # Replace with your actual Streamlit app URL
    "http://localhost:8501", # For local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. Pydantic Models ---
class Token(BaseModel):
    access_token: str
    token_type: str


# --- 6. API Endpoints ---

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Proxies the user's login request to the external Corpus API."""
    return await corpus_service.login_for_token(form_data.username, form_data.password)


@app.get("/crafts", tags=["Crafts"])
async def get_all_crafts():
    """Fetches all public craft records from the Corpus API."""
    return await corpus_service.get_all_crafts_from_corpus()


@app.post("/crafts", tags=["Crafts"])
async def upload_craft(
    token: Annotated[str, Depends(oauth2_scheme)],
    description: Annotated[str, Form()],
    category_id: Annotated[str, Form()],
    language: Annotated[str, Form()],
    release_rights: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
):
    """Uploads a new craft by sending all details to the Corpus API."""
    return await corpus_service.upload_craft_to_corpus(
        token=token,
        description=description,
        file=file,
        category_id=category_id,
        language=language,
        release_rights=release_rights,
    )