"""
Security utilities for LegalRAG authentication.
Handles bcrypt password hashing/verification and JWT token
creation/decoding. All secrets are loaded from environment variables.
"""

import os
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException
from fastapi import Depends
from typing import Annotated

#----------Import from other packages----------
from logs.logger import get_logger

load_dotenv()
logger = get_logger()
SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_KEY = os.getenv("REFRESH_KEY")
VERSION = os.getenv("API_VERSION", "v1")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/{VERSION}/auth/login")

def get_hashed_password(password: str) -> str:
    """
    Helper function to hash a password
    :param password: Original password
    :return: Hashed password
    """
    try:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Got an error during hashing of password:{e}")
        raise ValueError("Got an error during hashing of password")

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Check if the password and hashed_password is same or not
    :param password: Plain password
    :param hashed_password: Hashed password
    :return: True or False
    """
    try:
        password_bytes = password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        result = bcrypt.checkpw(password_bytes, hashed_password_bytes)
        return result
    except Exception as e:
        logger.error(f"Got an error during verification of password and hashed password:{e}")
        raise ValueError("Got an error during verification of password and hashed password")

def create_access_token(data: dict) -> str:
    """
    To create the JWT token using the payload, secret key and algorithm
    :param data: User's data
    :return: JWT token
    """
    try:
        if not data:
            logger.error("No data found on the payload")
            raise ValueError("No data found on the payload")
        data["exp"] = datetime.now(timezone.utc) + timedelta(hours=1)
        token = jwt.encode(data,SECRET_KEY,algorithm="HS256")
        return token
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to generate JWT token:{e}")
        raise RuntimeError("Failed to generate JWT token")

def create_refresh_token(data: dict) -> str:
    """
    To create the JWT token using the payload, refresh secret key and algorithm
    :param data: User's data
    :return: JWT token
    """
    try:
        if not data:
            raise ValueError("No data found on the payload")
        to_encode = data.copy()
        to_encode["exp"] = datetime.now(timezone.utc) + timedelta(days=7)
        token = jwt.encode(to_encode, REFRESH_KEY, algorithm="HS256")
        return token
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to generate refresh token: {e}")
        raise RuntimeError("Failed to generate refresh token")

def decode_access_token(token: str) -> dict:
    """
    To decode the JWT token and return the payload
    :param token: token send by user
    :return: payload
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise ExpiredSignatureError("Token has expired")
    except InvalidTokenError:
        raise InvalidTokenError("Invalid token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    Extracts and validates the JWT token from the request header.
    Decodes the token and returns the payload if valid.
    :param token: Bearer token extracted from Authorization header.
    :return: Decoded JWT payload containing email and role.
    """
    try:
        payload = decode_access_token(token)
        return payload
    except (ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Got some error while decoding the JWT token:{e}")
        raise HTTPException(status_code=500, detail="Encountered some error, kindly try again after some time")

async def require_admin(current_user: Annotated[dict,Depends(get_current_user)]) -> dict:
    """
    Verifies the current user has admin role.
    Depends on get_current_user for token validation.

    :param current_user: Decoded JWT payload from get_current_user.
    :return: Current user payload if admin, else raises 403.
    """
    try:
        if current_user.get('role') != 'admin':
            logger.error("User is not authorized")
            raise HTTPException(
                status_code=403,
                detail="You are not authorized"
            )
        return current_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Got some error while checking role:{e}")
        raise ValueError("Encountered some error, kindly try again after some time")