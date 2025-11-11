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
    
    # Check file size (1GB = 1073741824 bytes)
    MAX_FILE_SIZE = 1073741824
    file_content = None
    
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size / (1024*1024):.2f} MB) exceeds the maximum allowed size of 1GB"
            )
        
        # Store file content - it's already read, no need to read again
        # We'll use this file_content later for the upload
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read file: {str(e)}")
    
    # Ensure file_content was successfully read
    if file_content is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read file content")
    
    # Get the user's ID from their token to associate with the upload.
    user_data = await get_user_from_token(token)
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not determine user ID for upload.")

    # Get content type with fallback for None values
    content_type = file.content_type or "application/octet-stream"

    # Use requests library directly for better multipart form handling
    import requests
    
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
        
        # Use file_content that was already read during size check
        # We already have file_content from the size validation above
        
        # Prepare form data (all fields as strings)
        form_data = {}
        for key, value in data.items():
            form_data[key] = str(value)
        
        # Prepare files
        files_data = {
            'file': (file.filename, file_content, content_type)
        }
        
        # Prepare headers
        headers = {"Authorization": f"Bearer {token}"}
        
        logger.info(f"DEBUG - Upload URL: {UPLOAD_URL}")
        logger.info(f"DEBUG - Form data keys: {list(form_data.keys())}")
        logger.info(f"DEBUG - Form data values: {form_data}")
        logger.info(f"DEBUG - Files: {list(files_data.keys())}")
        logger.info(f"DEBUG - Headers: {headers}")
        
        # Try different approaches for sending data
        logger.info("DEBUG - Attempting upload with form data")
        
        # Method 1: Try with form data and files
        try:
            response = requests.post(UPLOAD_URL, data=form_data, files=files_data, headers=headers, timeout=60)
            response.raise_for_status()
            logger.info("DEBUG - Upload successful with form data")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.warning(f"DEBUG - Form data failed: {e.response.status_code} - {e.response.text}")
            
            # Method 2: Try with JSON data (without file first)
            logger.info("DEBUG - Trying with JSON data")
            try:
                json_headers = headers.copy()
                json_headers["Content-Type"] = "application/json"
                
                # Remove file from data for JSON
                json_data = data.copy()
                
                response = requests.post(UPLOAD_URL, json=json_data, headers=json_headers, timeout=60)
                response.raise_for_status()
                logger.info("DEBUG - Upload successful with JSON data")
                return response.json()
            except requests.exceptions.HTTPError as e2:
                logger.warning(f"DEBUG - JSON data failed: {e2.response.status_code} - {e2.response.text}")
                
                # Method 3: Try with multipart/form-data explicitly
                logger.info("DEBUG - Trying with explicit multipart")
                try:
                    # Create a proper multipart form
                    from requests_toolbelt.multipart.encoder import MultipartEncoder
                    
                    multipart_data = MultipartEncoder(
                        fields={
                            **form_data,
                            'file': (file.filename, file_content, content_type)
                        }
                    )
                    
                    multipart_headers = headers.copy()
                    multipart_headers['Content-Type'] = multipart_data.content_type
                    
                    response = requests.post(UPLOAD_URL, data=multipart_data, headers=multipart_headers, timeout=60)
                    response.raise_for_status()
                    logger.info("DEBUG - Upload successful with explicit multipart")
                    return response.json()
                except Exception as e3:
                    logger.error(f"DEBUG - Explicit multipart failed: {str(e3)}")
                    raise e  # Re-raise the original error
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"Corpus API HTTP error: {e.response.status_code}")
        logger.error(f"Corpus API error response: {e.response.text}")
        logger.error(f"Request data sent: {data}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Corpus API upload failed: {e.response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to connect to Corpus API: {str(e)}")