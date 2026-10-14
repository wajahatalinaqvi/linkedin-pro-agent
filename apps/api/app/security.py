"""Password hashing and access tokens. Production needs OAuth + refresh/revocation."""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"

def secret() -> str:
    value = os.environ.get("JWT_SECRET", "")
    if len(value) < 32:
        raise RuntimeError("JWT_SECRET must be configured with at least 32 random characters.")
    return value

def issue_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "iat": now, "exp": now + timedelta(hours=8),
         "iss": "linkedin-pro-saas", "aud": "linkedin-pro-web"},
        secret(), algorithm=ALGORITHM,
    )

def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(
            credentials.credentials, secret(), algorithms=[ALGORITHM],
            issuer="linkedin-pro-saas", audience="linkedin-pro-web",
        )
        user_id = payload.get("sub")
        user = db.get(User, user_id) if user_id else None
    except (jwt.PyJWTError, ValueError, TypeError):
        user = None
    if user is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return user
