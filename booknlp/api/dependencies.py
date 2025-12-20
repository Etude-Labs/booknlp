"""Authentication dependencies for BookNLP API."""

import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API key header dependency
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """Verify API key if authentication is required.
    
    Args:
        api_key: API key from request header
        
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If authentication is required but key is missing/invalid
    """
    # Check if authentication is required
    auth_required = os.getenv("BOOKNLP_AUTH_REQUIRED", "false").lower() == "true"
    
    if not auth_required:
        # Authentication disabled, allow access
        return None
    
    # Get expected API key from environment
    expected_key = os.getenv("BOOKNLP_API_KEY")
    if not expected_key:
        # This is a configuration error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: API key not configured",
        )
    
    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate API key using timing-safe comparison
    if not secrets.compare_digest(api_key or "", expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


# Optional dependency for endpoints that can work with or without auth
def optional_auth(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """Optional authentication that doesn't fail if auth is disabled.
    
    This is useful for endpoints that should work regardless of auth settings.
    """
    auth_required = os.getenv("BOOKNLP_AUTH_REQUIRED", "false").lower() == "true"
    
    if not auth_required:
        return None
    
    expected_key = os.getenv("BOOKNLP_API_KEY")
    if not expected_key or not api_key or not secrets.compare_digest(api_key, expected_key):
        return None
    
    return api_key
