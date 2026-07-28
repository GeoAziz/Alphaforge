"""
Firebase Admin SDK initialization for token verification in FastAPI.

Security model:
- Production: Requires valid Firebase ID token. No exceptions.
- Development: Allows unauthenticated access ONLY when ALLOW_UNAUTHENTICATED_DEV=true.
  This flag must be explicitly set — the default is to require auth even in dev.
"""

import os
import json
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Header
import logging
from config import Config

logger = logging.getLogger(__name__)

# Explicit dev bypass — must be opt-in, not default
_ALLOW_UNAUTHENTICATED_DEV = (
    os.getenv("ALLOW_UNAUTHENTICATED_DEV", "false").lower() == "true"
    and os.getenv("API_ENV", "development").lower() == "development"
)


class FirebaseTokenVerifier:
    """Firebase token verification singleton."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseTokenVerifier, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.firebase_enabled = False

        service_account_path = Config.FIREBASE_SERVICE_ACCOUNT_PATH

        try:
            if os.path.exists(service_account_path):
                with open(service_account_path, "r") as f:
                    creds_dict = json.load(f)

                creds = credentials.Certificate(creds_dict)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(creds)
                self.firebase_enabled = True
                logger.info("Firebase Admin SDK initialized")
            else:
                logger.warning(
                    "Service account key not found at %s — token verification disabled",
                    service_account_path,
                )

        except Exception as e:
            logger.error("Firebase Admin SDK initialization failed: %s", e)

    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify a Firebase ID token.

        Raises:
            HTTPException: 401 if token is invalid, expired, revoked, or Firebase
                           is not initialized.
        """
        if not firebase_admin._apps:
            raise HTTPException(
                status_code=503,
                detail="Authentication service not configured",
            )

        cleaned = token.replace("Bearer ", "").strip()
        if not cleaned:
            raise HTTPException(status_code=401, detail="Empty authentication token")

        try:
            decoded = auth.verify_id_token(cleaned)
            return decoded
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        except Exception as e:
            msg = str(e).lower()
            if "expired" in msg:
                raise HTTPException(status_code=401, detail="Authentication token expired")
            if "revoked" in msg:
                raise HTTPException(status_code=401, detail="Authentication token revoked")
            raise HTTPException(status_code=401, detail="Authentication failed")


def get_firebase_verifier() -> FirebaseTokenVerifier:
    """Get the singleton Firebase token verifier."""
    return FirebaseTokenVerifier()


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency: verify Firebase token, return user UID.

    Behavior:
      - Production: always requires a valid token.
      - Development with ALLOW_UNAUTHENTICATED_DEV=true: allows missing/invalid
        tokens with a demo-user fallback (for local dev convenience).
      - Development without that flag: requires a valid token just like production.

    Usage:
        @app.get("/api/protected")
        async def protected(user_id: str = Depends(verify_firebase_token)):
            ...
    """
    # Production — no exceptions
    if os.getenv("API_ENV", "development").lower() == "production":
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        verifier = get_firebase_verifier()
        decoded = verifier.verify_token(authorization)
        return decoded.get("uid", "unknown-user")

    # Development — explicit opt-in bypass (allows missing token, but validates if provided)
    if _ALLOW_UNAUTHENTICATED_DEV:
        if not authorization:
            logger.warning(
                "DEV MODE: No auth header — using demo-user "
                "(set ALLOW_UNAUTHENTICATED_DEV=false to enforce auth)"
            )
            return "demo-user"
        verifier = get_firebase_verifier()
        if not verifier.firebase_enabled:
            logger.warning("DEV MODE: Firebase not available, using token as-is")
            return authorization.replace("Bearer ", "").strip()[:20]
        try:
            decoded = verifier.verify_token(authorization)
            return decoded.get("uid", "unknown-user")
        except HTTPException as e:
            raise HTTPException(status_code=e.status_code, detail=e.detail)

    # Development — default: enforce auth (same as production)
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    verifier = get_firebase_verifier()
    decoded = verifier.verify_token(authorization)
    return decoded.get("uid", "unknown-user")


async def verify_firebase_token_optional(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Soft verification for endpoints that support anonymous access.
    Returns user_id if token is valid, otherwise a demo user.
    Never silently swallows real auth errors in production.
    """
    if not authorization:
        if os.getenv("API_ENV", "development").lower() == "development":
            return "demo-user"
        raise HTTPException(status_code=401, detail="Missing authorization header")

    verifier = get_firebase_verifier()
    if not verifier.firebase_enabled:
        if os.getenv("API_ENV", "development").lower() == "development":
            return "demo-user"
        raise HTTPException(
            status_code=503,
            detail="Authentication service not configured",
        )

    try:
        decoded = verifier.verify_token(authorization)
        return decoded.get("uid", "demo-user")
    except HTTPException:
        if os.getenv("API_ENV", "development").lower() == "development":
            return "demo-user"
        raise
