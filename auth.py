import os
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Default secret key used for development; logs warning if not overridden
DEFAULT_SECRET = "super_secret_local_key_123"
SECRET_KEY = os.environ.get("JWT_SECRET", DEFAULT_SECRET)
if SECRET_KEY == DEFAULT_SECRET:
    import logging
    logging.warning("⚠️ SECURITY WARNING: Using default insecure JWT_SECRET. Set JWT_SECRET in your .env file.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

# Bcrypt hashing context for password storage and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 password bearer scheme pointing to the authentication endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Verifies that a plaintext candidate password matches the stored bcrypt hash
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Computes a salted bcrypt hash for a plaintext password
def get_password_hash(password):
    return pwd_context.hash(password)

# Encodes and signs user identity into an expiring JWT access token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Extracts, decodes, and verifies the JWT bearer token to authenticate requests
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    return username
