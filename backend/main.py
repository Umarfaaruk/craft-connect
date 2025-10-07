# backend/main.py
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from services import corpus_service

load_dotenv()
app = FastAPI(title="Craft Connect API (Live)")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

origins = [
    "https://your-streamlit-app-name.streamlit.app", # IMPORTANT: Replace with your actual Streamlit URL
    "http://localhost:8501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return await corpus_service.login_for_token(form_data.username, form_data.password)

@app.get("/crafts", tags=["Crafts"])
async def get_all_crafts():
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
    return await corpus_service.upload_craft_to_corpus(
        token=token, description=description, file=file,
        category_id=category_id, language=language, release_rights=release_rights,
    )