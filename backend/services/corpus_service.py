# backend/services/corpus_service.py
import os
import httpx
import uuid
import logging
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
SWECHA_API_BASE_URL = os.getenv("SWECHA_API_BASE_URL", "https://api.corpus.swecha.org")

TOKEN_URL = f"{SWECHA_API_BASE_URL}/api/v1/auth/login"
REGISTER_URL = f"{SWECHA_API_BASE_URL}/api/v1/auth/register"
ME_URL = f"{SWECHA_API_BASE_URL}/api/v1/auth/me"
RECORDS_URL = f"{SWECHA_API_BASE_URL}/api/v1/records/"
UPLOAD_URL = f"{SWECHA_API_BASE_URL}/api/v1/records/upload"

async def register_user(username: str, password: str, email: str = None) -> dict:
    """
    Registers a new user with the Corpus API.
    Returns the access token if successful.
    """
    # Validate inputs
    if not username or not username.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required")
    
    if not password or not password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")
    
    username = username.strip()
    password = password.strip()
    
    logger.info(f"Attempting to register user: {username}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Prepare registration data
            registration_data = {
                "username": username,
                "password": password,
            }
            
            # Add email if provided
            if email and email.strip():
                registration_data["email"] = email.strip()
            
            logger.info(f"Sending registration request to: {REGISTER_URL}")
            response = await client.post(REGISTER_URL, data=registration_data)
            logger.info(f"Registration response status: {response.status_code}")
            logger.info(f"Registration response: {response.text}")
            
            response.raise_for_status()
            response_data = response.json()
            
            # Handle different response formats
            if "access_token" in response_data:
                return {
                    "access_token": response_data["access_token"],
                    "token_type": response_data.get("token_type", "bearer")
                }
            elif "token" in response_data:
                return {
                    "access_token": response_data["token"],
                    "token_type": response_data.get("token_type", "bearer")
                }
            else:
                # If no token in response, try to login immediately
                logger.info("No token in registration response, attempting login...")
                return await login_for_token(username, password)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            logger.error(f"Error response: {e.response.text}")
            error_detail = "Registration failed. Please try again."
            try:
                error_body = e.response.json()
                if "detail" in error_body:
                    error_detail = error_body["detail"]
                elif "message" in error_body:
                    error_detail = error_body["message"]
                elif isinstance(error_body, str):
                    error_detail = error_body
            except:
                pass
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to connect to Corpus API: {str(e)}")

async def login_for_token(username: str, password: str) -> dict:
    """
    Logs in to the external Corpus API by sending credentials.
    Returns the access token if successful.
    """
    # Validate inputs - trim whitespace and check for empty values
    if not username or not username.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username (phone) is required")
    
    if not password or not password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")
    
    # Trim the inputs
    username = username.strip()
    password = password.strip()
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {"phone": username, "password": password}
            headers = {"Content-Type": "application/json"}
            
            logger.info(f"Attempting login to: {TOKEN_URL}")
            logger.info(f"Payload: phone={username}")
            
            response = await client.post(TOKEN_URL, json=payload, headers=headers, timeout=30.0)
            
            logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            # Extract the response data
            response_data = response.json()
            
            logger.info(f"Response data keys: {list(response_data.keys())}")
            
            # Handle different possible response formats
            if "access_token" in response_data:
                # If the API returns access_token, return it with token_type
                return {
                    "access_token": response_data["access_token"],
                    "token_type": "bearer"
                }
            elif "token" in response_data:
                # If the API returns just token, format it properly
                return {
                    "access_token": response_data["token"],
                    "token_type": "bearer"
                }
            else:
                # Return the raw response if it doesn't match expected formats
                return response_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            logger.error(f"Error response: {e.response.text}")
            error_detail = "Login failed. Please check your credentials."
            try:
                error_body = e.response.json()
                if "detail" in error_body:
                    error_detail = error_body["detail"]
                elif "message" in error_body:
                    error_detail = error_body["message"]
                elif isinstance(error_body, str):
                    error_detail = error_body
            except:
                pass
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_detail)
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to connect to Corpus API: {str(e)}")

async def get_user_from_token(token: str) -> dict:
    """
    Gets the current user's data from the Corpus API using a token.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is required")
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(ME_URL, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = "Could not validate token with Corpus API"
            try:
                error_body = e.response.json()
                if "detail" in error_body:
                    error_detail = error_body["detail"]
            except:
                pass
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_detail)
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to connect to Corpus API: {str(e)}")

async def get_all_crafts_from_corpus() -> list:
    """
    Fetches all public craft records from the Corpus API.
    Returns an empty list if the endpoint is not accessible or requires authentication.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Note: This assumes the /records endpoint is public.
            response = await client.get(RECORDS_URL)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                # If forbidden, return empty list - gallery will show "empty" message
                logger.warning("Corpus API returned 403 Forbidden. The /records endpoint may require authentication.")
                return []
            elif e.response.status_code == 404:
                # If not found, return empty list
                logger.warning("Corpus API endpoint not found. Returning empty list.")
                return []
            else:
                raise HTTPException(status_code=e.response.status_code, detail=f"Could not fetch crafts from Corpus API: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to connect to Corpus API: {str(e)}")

def get_media_type_from_content(content_type: str) -> str:
    """Determines the media type based on the file's content type."""
    if not content_type:
        return "text"
    content_type = content_type.lower()
    if "video" in content_type: return "video"
    if "audio" in content_type: return "audio"
    if "image" in content_type or "pdf" in content_type: return "image"
    return "text"

async def upload_craft_to_corpus(token: str, description: str, file: UploadFile, category_id: str, language: str, release_rights: str) -> dict:
    """
    Uploads a new craft to the Corpus API with all required fields.
    """
    # Validate inputs
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is required")
    
    if not file or not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is required")
    
    if not description:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Description is required")
    
    if not category_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category ID is required")
    
    if not language:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Language is required")
    
    if not release_rights:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Release rights is required")
    
    # Get the user's ID from their token to associate with the upload.
    user_data = await get_user_from_token(token)
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not determine user ID for upload.")

    # Get content type with fallback for None values
    content_type = file.content_type or "application/octet-stream"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Construct the complete data payload required by the Corpus API.
            data = {
                "title": file.filename,
                "description": description,
                "user_id": user_id,
                "category_id": category_id,
                "language": language,
                "release_rights": release_rights,
                "media_type": get_media_type_from_content(content_type),
                "upload_uuid": str(uuid.uuid4()),
                "filename": file.filename,
                "total_chunks": 1,
            }
            
            # Debug: Print data being sent to Corpus API
            logger.info(f"DEBUG - Data being sent to Corpus API: {data}")
            files = {"file": (file.filename, await file.read(), content_type)}
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await client.post(UPLOAD_URL, data=data, files=files, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Corpus API upload failed: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to connect to Corpus API: {str(e)}")