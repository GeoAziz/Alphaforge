"""
Firebase Admin SDK initialization for token verification in FastAPI.
Place this in backend/firebase_admin.py
"""

import os
import json
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Header
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class FirebaseTokenVerifier:
    """Helper class for Firebase token verification."""
    
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
        firebase_credentials = os.getenv("FIREBASE_CREDENTIALS_JSON")
        
        if firebase_credentials:
            try:
                creds_dict = json.loads(firebase_credentials)
                creds = credentials.Certificate(creds_dict)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(creds)
                logger.info("Firebase Admin SDK initialized successfully")
            except Exception as e:
                logger.warning(f"Firebase Admin SDK not available: {e}")
                logger.info("Using mock Firebase verification for development")
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify Firebase ID token and return decoded token.
        
        Args:
            token: Firebase ID token from Authorization header
            
        Returns:
            Decoded token dict with uid, email, etc.
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Remove "Bearer " prefix if present
            token = token.replace("Bearer ", "").strip()
            
            # Check if Firebase is initialized
            if not firebase_admin._apps:
                logger.warning("Firebase not initialized, using mock verification")
                # For development: accept any token format
                return {"uid": "dev-user", "email": "dev@example.com"}
            
            decoded_token = auth.verify_id_token(token)
            logger.info(f"Token verified for user: {decoded_token.get('uid')}")
            return decoded_token
            
        except firebase_admin.exceptions.InvalidIdTokenError as e:
            logger.error(f"Invalid ID token: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        except firebase_admin.exceptions.ExpiredIdTokenError as e:
            logger.error(f"Expired ID token: {e}")
            raise HTTPException(status_code=401, detail="Authentication token expired")
        except firebase_admin.exceptions.RevokedIdTokenError as e:
            logger.error(f"Revoked ID token: {e}")
            raise HTTPException(status_code=401, detail="Authentication token revoked")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")


def get_firebase_verifier() -> FirebaseTokenVerifier:
    """Get Firebase token verifier singleton instance."""
    return FirebaseTokenVerifier()


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency for verifying Firebase tokens in Authorization header.
    Returns user_id if token is valid.
    
    Usage:
        @app.get("/api/protected")
        async def protected_endpoint(user_id: str = Depends(verify_firebase_token)):
            return {"message": f"Hello {user_id}"}
    """
    if not authorization:
        # For development: allow requests without token
        if os.getenv("API_ENV") == "development":
            logger.warning("No authorization header provided, using demo user")
            return "demo-user"
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    verifier = get_firebase_verifier()
    decoded_token = verifier.verify_token(authorization)
    
    return decoded_token.get("uid", "unknown-user")


# Optional: Mock verification for testing
async def verify_firebase_token_optional(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Soft verification: returns user_id if token provided, otherwise demo user.
    Useful for endpoints that support both authenticated and anonymous access.
    """
    if not authorization:
        return "demo-user"
    
    try:
        verifier = get_firebase_verifier()
        decoded_token = verifier.verify_token(authorization)
        return decoded_token.get("uid", "demo-user")
    except HTTPException:
        # If token verification fails, still allow with demo user
        return "demo-user"
