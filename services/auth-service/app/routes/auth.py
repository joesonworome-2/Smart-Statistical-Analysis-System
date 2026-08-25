import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings
from app.database import users_collection
from app.models.user import create_user_document
from app.schemas.user import (
    GoogleLoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.security.dependencies import get_current_user
from app.security.jwt import create_access_token
from app.security.password import (
    hash_password,
    verify_password,
)
from app.security.refresh import (
    delete_refresh_token,
    generate_refresh_token,
    get_refresh_token_user,
    store_refresh_token,
)
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)



def create_google_username(email: str) -> str:
    """Create a unique SSAS username from a Google email."""

    local_part = email.split("@", 1)[0].lower()

    base = re.sub(
        r"[^a-z0-9_.-]",
        "",
        local_part,
    )

    if len(base) < 3:
        base = "googleuser"

    base = base[:40]

    candidate = base
    counter = 1

    while users_collection.find_one(
        {"username": candidate}
    ):
        suffix = f"_{counter}"

        candidate = (
            base[:50 - len(suffix)]
            + suffix
        )

        counter += 1

    return candidate


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user: UserRegister):

    # Check whether the email already exists
    existing_email = users_collection.find_one(
        {"email": user.email.lower()}
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    # Check whether username already exists
    existing_username = users_collection.find_one(
        {"username": user.username}
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )

    # Hash password
    hashed_password = hash_password(user.password)

    # Create MongoDB document
    user_document = create_user_document(
        email=user.email,
        username=user.username,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    # Insert user
    result = users_collection.insert_one(user_document)

    # Return safe user information
    return UserResponse(
        id=str(result.inserted_id),
        email=user_document["email"],
        username=user_document["username"],
        first_name=user_document["first_name"],
        last_name=user_document["last_name"],
        role=user_document["role"],
        is_active=user_document["is_active"],
    )

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(credentials: UserLogin):

    user = users_collection.find_one(
        {"email": credentials.email.lower()}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    password_is_valid = verify_password(
        credentials.password,
        user["password_hash"],
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Create access token
    access_token = create_access_token(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"],
    )

    # Create refresh token
    refresh_token = generate_refresh_token()

    # Store refresh token in Redis
    store_refresh_token(
        refresh_token,
        str(user["_id"]),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post(
    "/google",
    response_model=TokenResponse,
)
def google_login(request: GoogleLoginRequest):

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Sign-In is not configured.",
        )

    try:
        google_user = id_token.verify_oauth2_token(
            request.credential,
            google_requests.Request(),
            settings.google_client_id,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential.",
        )

    email = (
        google_user.get("email", "")
        .strip()
        .lower()
    )

    email_verified = google_user.get(
        "email_verified",
        False,
    )

    google_sub = google_user.get("sub")

    if not email or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Google account email "
                "could not be verified."
            ),
        )

    if not google_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google account.",
        )

    user = users_collection.find_one(
        {"email": email}
    )

    if user:

        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        stored_google_sub = user.get(
            "google_sub"
        )

        if (
            stored_google_sub
            and stored_google_sub != google_sub
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This email is already linked "
                    "to another Google account."
                ),
            )

        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "google_sub": google_sub,
                    "google_email_verified": True,
                }
            },
        )

    else:

        username = create_google_username(
            email
        )

        first_name = (
            google_user.get("given_name")
            or google_user.get("name")
            or "Google"
        )

        last_name = (
            google_user.get("family_name")
            or "User"
        )

        random_password = (
            secrets.token_urlsafe(48)
        )

        password_hash = hash_password(
            random_password
        )

        user_document = create_user_document(
            email=email,
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )

        user_document.update(
            {
                "auth_provider": "google",
                "google_sub": google_sub,
                "google_email_verified": True,
                "profile_picture": google_user.get(
                    "picture"
                ),
            }
        )

        result = users_collection.insert_one(
            user_document
        )

        user_document["_id"] = (
            result.inserted_id
        )

        user = user_document

    access_token = create_access_token(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"],
    )

    refresh_token = generate_refresh_token()

    store_refresh_token(
        refresh_token,
        str(user["_id"]),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=(
            settings
            .jwt_access_token_expire_minutes
            * 60
        ),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_access_token(request: RefreshTokenRequest):

    session = get_refresh_token_user(
        request.refresh_token
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user_id = session["user_id"]

    from bson import ObjectId

    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    user = users_collection.find_one(
        {"_id": object_id}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    access_token = create_access_token(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"],
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )

@router.post(
    "/logout",
    response_model=MessageResponse,
)
def logout(request: RefreshTokenRequest):

    session = get_refresh_token_user(
        request.refresh_token
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    delete_refresh_token(
        request.refresh_token
    )

    return MessageResponse(
        message="Successfully logged out."
    )

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(current_user=Depends(get_current_user)):

    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        username=current_user["username"],
        first_name=current_user["first_name"],
        last_name=current_user["last_name"],
        role=current_user["role"],
        is_active=current_user["is_active"],
    )

