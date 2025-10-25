# backend/main.py

# --- Standard Library and Third-party Imports ---
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# --- Local Application Imports ---
from services import corpus_service

# --- 1. Configuration ---
load_dotenv()

# --- 2. Create the FastAPI App Instance ---
app = FastAPI(title="Craft Connect API (Final)")

# --- 3. Security Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- 4. CORS Middleware ---
# Allow all origins for development and deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
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
    """
    Proxies the user's login request to the external Corpus API.
    """
    return await corpus_service.login_for_token(form_data.username, form_data.password)

@app.post("/auth/register", response_model=Token, tags=["Authentication"])
async def register(username: str = Form(), password: str = Form(), email: str = Form(None)):
    """
    Registers a new user with the Corpus API.
    """
    return await corpus_service.register_user(username, password, email)


@app.get("/crafts", tags=["Crafts"])
async def get_all_crafts():
    """
    Fetches all public craft records from the Corpus API.
    """
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
    """
    Uploads a new craft by sending all details to the Corpus API.
    """
    # Debug: Print received parameters (remove after testing)
    # print(f"DEBUG - Received parameters:")
    # print(f"  description: {description}")
    # print(f"  category_id: {category_id}")
    # print(f"  language: {language}")
    # print(f"  release_rights: {release_rights}")
    # print(f"  file: {file.filename}")
    
    return await corpus_service.upload_craft_to_corpus(
        token=token,
        description=description,
        file=file,
        category_id=category_id,
        language=language,
        release_rights=release_rights,
    )