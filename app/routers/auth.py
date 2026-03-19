"""
Authentication router for LegalRAG.
Handles user registration, login, and current user retrieval.
JWT tokens are issued on login and validated on protected routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

#---------Import from other packages-----------
from logs.logger import get_logger
from app.common.user_model import UserRegister, UserLogin, UserResponse, DBUser, RefreshRequest
from app.core.security import (
    get_hashed_password, verify_password,
    create_access_token,create_refresh_token,
    get_current_user, decode_access_token
)
from app.utils.mongo import get_user_cred

logger = get_logger()
limiter = Limiter(key_func=get_remote_address)
auth_router = APIRouter()

#--------------Routers------------------
@auth_router.post("/register",tags=['Authentication'])
@limiter.limit("5/minute" )
def get_registered(request: Request,input: UserRegister) -> dict:
    """
    Register a new user account.
    Checks if the email already exists, hashes the password,
    and stores the new user in MongoDB with default role 'user'.

    :param input: Registration payload with fullname, email, password.
    :return: Success message on successful registration.
    """
    try:
        fullname = input.fullname
        email = input.email
        password = input.password

        collection = get_user_cred()
        is_present = collection.find_one({"email": email}, {"_id": 0})
        if is_present is not None:
            raise HTTPException(status_code=400,detail="Email already exists")

        hashed_password = get_hashed_password(password)
        user_cred = {
            'fullname':fullname,
            'email':email,
            'password':hashed_password,
        }
        user = DBUser(**user_cred)
        mongo_data = user.model_dump()
        collection.insert_one(mongo_data)

        logger.info("Registered user's cred on DB")
        return {"message":"Registered Successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Got some error while registering user:{e}")
        raise RuntimeError("Encountered some error, kindly try again after some time")

@auth_router.post("/login",tags=['Authentication'])
@limiter.limit("5/minute" )
def get_login(request: Request,input: UserLogin) -> UserResponse:
    """
    Authenticate a user and return a JWT access token.
    Verifies the email exists and the password matches,
    then generates a signed token with user identity and role.

    :param input: Login payload with email and password.
    :return: JWT access token wrapped in UserResponse.
    """
    try:
        email = input.email
        password = input.password

        collection = get_user_cred()
        mongo_result = collection.find_one(
            {"email": email},
            {"_id": 0,'password':1,'role':1})

        if not mongo_result:
            raise HTTPException(status_code=401,detail="Sorry we did not found your credential")

        hashed_password = mongo_result.get('password')
        role = mongo_result.get('role')

        result =  verify_password(password, hashed_password)
        if not result:
            logger.error("Password did not match")
            raise HTTPException(status_code=401,detail="Password did not match")

        data = {
            'email':email,
            'role': role
        }
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        collection.update_one(
            {"email": email},
            {"$set": {"refresh_token": refresh_token}}
        )

        return UserResponse(access_token=access_token, refresh_token=refresh_token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Got some error while logging:{e}")
        raise RuntimeError("Encountered some error, kindly try again after some time")

@auth_router.get("/me", tags=["Authentication"])
@limiter.limit("30/minute" )
def get_me(request: Request,payload: dict = Depends(get_current_user)) -> dict:
    """
    Returns the current authenticated user's information.
    Extracts user details from the validated JWT token payload.

    :param payload: Decoded JWT payload from get_current_user dependency.
    :return: Current user's email and role.
    """
    return {
        "email": payload.get("email"),
        "role": payload.get("role")
    }

@auth_router.post("/refresh", tags=["Authentication"])
@limiter.limit("10/minute")
def refresh_token(request: Request, body: RefreshRequest) -> UserResponse:
    try:
        collection = get_user_cred()

        user = collection.find_one(
            {"refresh_token": body.refresh_token},
            {"_id": 0, "email": 1, "role": 1}
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        try:
            decode_access_token(body.refresh_token)
        except Exception:
            collection.update_one(
                {"email": user["email"]},
                {"$set": {"refresh_token": None}}
            )
            raise HTTPException(status_code=401, detail="Refresh token expired or invalid")

        data = {"email": user["email"], "role": user["role"]}
        new_access_token = create_access_token(data)
        new_refresh_token = create_refresh_token(data)

        collection.update_one(
            {"email": user["email"]},
            {"$set": {"refresh_token": new_refresh_token}}
        )

        return UserResponse(access_token=new_access_token, refresh_token=new_refresh_token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {e}")
        raise RuntimeError("Encountered some error, kindly try again after some time")


@auth_router.post("/logout", tags=["Authentication"])
@limiter.limit("10/minute")
def logout(request: Request, payload: dict = Depends(get_current_user)) -> dict:
    try:
        email = payload.get("email")
        collection = get_user_cred()
        collection.update_one(
            {"email": email},
            {"$set": {"refresh_token": None}}
        )
        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise RuntimeError("Encountered some error, kindly try again after some time")
