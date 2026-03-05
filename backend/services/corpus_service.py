"""
Corpus Service — Backend API Bridge
====================================

This module acts as the bridge between the Craft Connect FastAPI backend
and the external **Swecha Corpus API** (https://api.corpus.swecha.org).

It handles:
    • User authentication (login & registration)
    • Token-based user identity verification
    • Fetching public craft records for the gallery
    • Fetching category metadata
    • Uploading new crafts (with file attachments)

Environment Variables:
    SWECHA_API_BASE_URL  — Base URL of the Corpus API (default: https://api.corpus.swecha.org)
    SWECHA_CATEGORIES_URL — Override URL for the categories endpoint (optional)

Dependencies:
    httpx               — Async HTTP client for auth / read operations
    requests            — Sync HTTP client for multipart file uploads
    requests-toolbelt   — Helper for multipart encoding (available, used if needed)
"""

# ──────────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────────
import os
import uuid
import logging
from typing import Any, Dict, List, Optional

import httpx                          # Async HTTP client (auth & reads)
import requests                       # Sync HTTP client (file uploads)
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

# Logger for this module — all log messages use the module name for filtering
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

# Swecha Corpus API endpoints
SWECHA_API_BASE_URL = os.getenv("SWECHA_API_BASE_URL", "https://api.corpus.swecha.org")

TOKEN_URL      = f"{SWECHA_API_BASE_URL}/api/v1/auth/login"       # POST — login with phone+password
REGISTER_URL   = f"{SWECHA_API_BASE_URL}/api/v1/auth/register"    # POST — create new account
ME_URL         = f"{SWECHA_API_BASE_URL}/api/v1/auth/me"          # GET  — get current user info
RECORDS_URL    = f"{SWECHA_API_BASE_URL}/api/v1/records/"         # GET  — list all public records
UPLOAD_URL     = f"{SWECHA_API_BASE_URL}/api/v1/records/upload"   # POST — upload a new record
CATEGORIES_URL = os.getenv(                                        # GET  — list all categories
    "SWECHA_CATEGORIES_URL",
    f"{SWECHA_API_BASE_URL}/api/v1/categories",
)

# Upload constraints
MAX_FILE_SIZE_BYTES = 1_073_741_824   # 1 GB
DEFAULT_TIMEOUT     = 30.0            # seconds — used for all API calls
UPLOAD_TIMEOUT      = 120             # seconds — longer timeout for file uploads


# ══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

async def register_user(
    username: str,
    password: str,
    email: Optional[str] = None,
) -> Dict[str, str]:
    """
    Register a new user account on the Corpus API.

    The Corpus API expects ``username`` to be a **phone number**.
    If the API doesn't return a token directly, we automatically
    attempt a login to obtain one.

    Args:
        username: Phone number of the new user.
        password: Account password.
        email:    Optional email address.

    Returns:
        dict with ``access_token`` and ``token_type`` keys.

    Raises:
        HTTPException 400: Invalid input or API rejection.
        HTTPException 503: Corpus API is unreachable.
    """
    # ── Input validation ──
    if not username or not username.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required")
    if not password or not password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")

    username = username.strip()
    password = password.strip()
    logger.info("Registering new user: %s", username)

    # ── Call Corpus API ──
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            form_data: Dict[str, str] = {"username": username, "password": password}
            if email and email.strip():
                form_data["email"] = email.strip()

            response = await client.post(REGISTER_URL, data=form_data)
            response.raise_for_status()
            body = response.json()

            # The API may return the token under different keys
            token = body.get("access_token") or body.get("token")
            if token:
                return {
                    "access_token": token,
                    "token_type": body.get("token_type", "bearer"),
                }

            # No token in response → try logging in immediately
            logger.info("No token in registration response — attempting auto-login")
            return await login_for_token(username, password)

        except httpx.HTTPStatusError as exc:
            logger.error("Registration failed (%s): %s", exc.response.status_code, exc.response.text)
            detail = _extract_error_detail(exc, fallback="Registration failed. Please try again.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot reach Corpus API: {exc}",
            )


async def login_for_token(username: str, password: str) -> Dict[str, str]:
    """
    Authenticate an existing user and retrieve an access token.

    The Corpus API login endpoint expects a JSON body with
    ``phone`` (not ``username``) and ``password``.

    Args:
        username: Phone number used during registration.
        password: Account password.

    Returns:
        dict with ``access_token`` and ``token_type`` keys.

    Raises:
        HTTPException 400: Missing credentials.
        HTTPException 401: Wrong username/password.
        HTTPException 503: Corpus API is unreachable.
    """
    # ── Input validation ──
    if not username or not username.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username (phone) is required")
    if not password or not password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")

    username = username.strip()
    password = password.strip()

    # ── Call Corpus API ──
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            # NOTE: The Corpus API expects the field name "phone", not "username"
            payload = {"phone": username, "password": password}
            response = await client.post(
                TOKEN_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            body = response.json()

            # Normalise different token field names
            token = body.get("access_token") or body.get("token")
            if token:
                return {"access_token": token, "token_type": "bearer"}

            # Unexpected shape — return raw response (caller may handle it)
            return body

        except httpx.HTTPStatusError as exc:
            logger.error("Login failed (%s): %s", exc.response.status_code, exc.response.text)
            detail = _extract_error_detail(exc, fallback="Login failed. Please check your credentials.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot reach Corpus API: {exc}",
            )


async def get_user_from_token(token: str) -> Dict[str, Any]:
    """
    Retrieve the authenticated user's profile from the Corpus API.

    This is used internally to obtain the ``user_id`` needed when
    uploading crafts.

    Args:
        token: Bearer access token obtained during login/registration.

    Returns:
        dict containing user profile fields (at minimum ``id``).

    Raises:
        HTTPException 401: Token is missing or invalid.
        HTTPException 503: Corpus API is unreachable.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is required")

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(ME_URL, headers=_auth_header(token))
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as exc:
            detail = _extract_error_detail(exc, fallback="Could not validate token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot reach Corpus API: {exc}",
            )


# ══════════════════════════════════════════════════════════════════════════════
#  CRAFT RECORDS  (read)
# ══════════════════════════════════════════════════════════════════════════════

async def get_all_crafts_from_corpus() -> List[Any]:
    """
    Fetch every public craft record from the Corpus API.

    The ``/records/`` endpoint may return **403 Forbidden** if it
    requires authentication, or **404** if the endpoint doesn't exist.
    In both cases we gracefully return an empty list so the gallery
    page can display an "empty" message instead of crashing.

    Returns:
        List of craft record dicts, or an empty list.
    """
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(RECORDS_URL)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (403, 404):
                logger.warning("Records endpoint returned %s — returning empty list", exc.response.status_code)
                return []
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Could not fetch crafts: {exc.response.text}",
            )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot reach Corpus API: {exc}",
            )


async def get_categories_from_corpus() -> List[Dict[str, Any]]:
    """
    Fetch the list of craft categories from the Corpus API.

    The API may return one of several shapes:
        • A plain list ``[{id, name}, ...]``
        • An object ``{"results": [...]}`` or ``{"data": [...]}``

    We normalise all of these into a flat list before returning.

    Returns:
        List of category dicts, each with at least ``id`` and ``name``.

    Raises:
        HTTPException 502: Response format is unrecognised.
        HTTPException 503: Corpus API is unreachable.
    """
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(CATEGORIES_URL)
            response.raise_for_status()
            data = response.json()

            # Normalise response shape
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ("results", "data"):
                    if key in data:
                        return data[key]

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected categories response format from Corpus API",
            )

        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Failed to fetch categories: {exc.response.text}",
            )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot reach Corpus API: {exc}",
            )


# ══════════════════════════════════════════════════════════════════════════════
#  CRAFT UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

async def upload_craft_to_corpus(
    token: str,
    description: str,
    file: UploadFile,
    category_id: str,
    language: str,
    release_rights: str,
) -> Dict[str, Any]:
    """
    Upload a new craft record (with an attached file) to the Corpus API.

    Workflow:
        1. Validate all required fields.
        2. Read the file into memory and check size (max 1 GB).
        3. Resolve the uploader's ``user_id`` from their token.
        4. Build a multipart form payload with all metadata + file.
        5. POST to the Corpus ``/records/upload`` endpoint.

    Args:
        token:          Bearer token of the authenticated uploader.
        description:    Human-readable description (also used as ``title``).
        file:           The uploaded file (image or video).
        category_id:    ID of the craft category.
        language:       Language code (e.g. ``"telugu"``, ``"NA"``).
        release_rights: One of ``"creator"``, ``"others"``, ``"downloaded"``, ``"NA"``.

    Returns:
        The JSON response from the Corpus API on success.

    Raises:
        HTTPException 400: Missing/invalid input or unreadable file.
        HTTPException 401: Invalid token.
        HTTPException 403: Cannot determine user ID.
        HTTPException 413: File exceeds 1 GB.
        HTTPException 503: Corpus API is unreachable.
    """
    # ── 1. Validate inputs ──
    _require(token, "Token is required", status.HTTP_401_UNAUTHORIZED)
    _require(file and file.filename, "File is required")
    _require(description, "Description is required")
    _require(category_id, "Category ID is required")
    _require(language, "Language is required")
    _require(release_rights, "Release rights is required")

    # ── 2. Read file & enforce size limit ──
    try:
        file_content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {exc}",
        )

    file_size_mb = len(file_content) / (1024 * 1024)
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size_mb:.1f} MB) exceeds the 1 GB limit",
        )

    logger.info("File accepted: %s (%.1f MB)", file.filename, file_size_mb)

    # ── 3. Resolve uploader identity ──
    user_data = await get_user_from_token(token)
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not determine user ID for upload",
        )

    # ── 4. Build multipart form payload ──
    content_type = file.content_type or "application/octet-stream"

    form_fields: Dict[str, str] = {
        "title":          description,                           # Corpus API requires ≥2 meaningful words
        "description":    description,
        "user_id":        str(user_id),
        "category_id":    str(category_id),
        "language":       language,
        "release_rights": release_rights,
        "media_type":     _detect_media_type(content_type),      # "image", "video", "audio", or "text"
        "upload_uuid":    str(uuid.uuid4()),                     # Unique ID for this upload session
        "filename":       file.filename,
        "total_chunks":   "1",                                   # We upload in a single chunk
    }

    files_payload = {
        "file": (file.filename, file_content, content_type),
    }

    logger.info("Uploading craft '%s' → %s", description[:60], UPLOAD_URL)

    # ── 5. POST to Corpus API ──
    try:
        response = requests.post(
            UPLOAD_URL,
            data=form_fields,
            files=files_payload,
            headers=_auth_header(token),
            timeout=UPLOAD_TIMEOUT,
        )
        response.raise_for_status()
        logger.info("Upload successful — record created")
        return response.json()

    except requests.exceptions.HTTPError as exc:
        logger.error("Upload failed (%s): %s", exc.response.status_code, exc.response.text)
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Corpus API upload failed: {exc.response.text}",
        )

    except requests.exceptions.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot reach Corpus API: {exc}",
        )


# ══════════════════════════════════════════════════════════════════════════════
#  PRIVATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _auth_header(token: str) -> Dict[str, str]:
    """Return an ``Authorization: Bearer <token>`` header dict."""
    return {"Authorization": f"Bearer {token}"}


def _detect_media_type(content_type: str) -> str:
    """
    Map a MIME content-type string to a simplified media type label.

    Examples:
        ``"image/png"``         → ``"image"``
        ``"video/mp4"``         → ``"video"``
        ``"audio/mpeg"``        → ``"audio"``
        ``"application/pdf"``   → ``"image"``   (treated as visual content)
        ``"text/plain"``        → ``"text"``
    """
    if not content_type:
        return "text"
    ct = content_type.lower()
    if "video" in ct:
        return "video"
    if "audio" in ct:
        return "audio"
    if "image" in ct or "pdf" in ct:
        return "image"
    return "text"


def _require(
    value: Any,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> None:
    """Raise ``HTTPException`` if *value* is falsy."""
    if not value:
        raise HTTPException(status_code=status_code, detail=message)


def _extract_error_detail(
    exc: httpx.HTTPStatusError,
    *,
    fallback: str = "An error occurred",
) -> str:
    """
    Try to pull a human-readable error message from an HTTP error response.

    Checks for ``detail`` and ``message`` keys in the JSON body, and
    falls back to the provided *fallback* string if nothing is found.
    """
    try:
        body = exc.response.json()
        return body.get("detail") or body.get("message") or fallback
    except Exception:
        return fallback