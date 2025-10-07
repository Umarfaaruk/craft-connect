# backend/services/corpus_service.py
import os
import httpx
import uuid
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status

load_dotenv()
SWECHA_API_BASE_URL = os.getenv("SWECHA_API_BASE_URL", "https://api.corpus.swecha.org")

TOKEN_URL = f"{SWECHA_API_BASE_URL}/api/v1/auth/login"
ME_URL = f"{SWECHA_API_BASE_URL}/api/v1/auth/me"
RECORDS_URL = f"{SWECHA_API_BASE_URL}/api/v1/records/"
UPLOAD_URL = f"{SWECHA_API_BASE_URL}/api/v1/records/upload"

async def login_for_token(username: str, password: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            payload = {"phone": username, "password": password}
            headers = {"Content-Type": "application/json"}
            response = await client.post(TOKEN_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

async def get_user_from_token(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(ME_URL, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate token with Corpus API")

async def get_all_crafts_from_corpus() -> list:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(RECORDS_URL)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Could not fetch crafts from Corpus API.")

def get_media_type_from_content(content_type: str) -> str:
    if "video" in content_type: return "video"
    if "audio" in content_type: return "audio"
    if "image" in content_type or "pdf" in content_type: return "image"
    return "text"

async def upload_craft_to_corpus(token: str, description: str, file: UploadFile, category_id: str, language: str, release_rights: str) -> dict:
    user_data = await get_user_from_token(token)
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Could not determine user ID for upload.")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            data = {
                "title": file.filename, "description": description, "user_id": user_id,
                "category_id": category_id, "language": language, "release_rights": release_rights,
                "media_type": get_media_type_from_content(file.content_type),
                "upload_uuid": str(uuid.uuid4()), "filename": file.filename, "total_chunks": 1,
            }
            files = {"file": (file.filename, await file.read(), file.content_type)}
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.post(UPLOAD_URL, data=data, files=files, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Corpus API upload failed: {e.response.text}")