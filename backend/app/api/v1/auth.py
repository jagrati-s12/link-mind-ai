from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_temp_2fa_token,
    decode_temp_2fa_token,
    generate_totp_secret,
    get_totp_uri,
    generate_qr_code_base64,
    verify_totp_code
)
from app.models import User, UserProfile
from app.schemas import (
    UserCreate,
    UserLogin,
    Token,
    LoginResponse,
    TOTPSetupResponse,
    TOTPVerifyRequest,
    TOTPLoginRequest,
    TOTPStatusResponse,
    UserOut
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=LoginResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name or "Student",
        is_totp_enabled=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create associated profile
    profile = UserProfile(user_id=user.id, target_roles=["Software Engineer"])
    db.add(profile)
    db.commit()

    token = create_access_token(user.id)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        requires_2fa=False,
        is_totp_enabled=False
    )

@router.post("/login", response_model=LoginResponse)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()

    # Auto-provision demo account if it doesn't exist yet
    if not user and user_in.email == "demo@linkmind.ai" and user_in.password == "password123":
        user = User(
            email="demo@linkmind.ai",
            hashed_password=hash_password("password123"),
            full_name="Demo User",
            is_totp_enabled=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        profile = UserProfile(user_id=user.id, target_roles=["AI Engineer", "Software Engineer"])
        db.add(profile)
        db.commit()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. If you don't have an account yet, click 'Create Account' above to sign up!"
        )

    # If user has 2FA enabled with Google Authenticator
    if user.is_totp_enabled:
        # Check if 6-digit code was already provided directly in login payload
        if user_in.code:
            if not verify_totp_code(user.totp_secret, user_in.code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google Authenticator verification code."
                )
            # Code verified successfully -> grant full token
            token = create_access_token(user.id)
            return LoginResponse(
                access_token=token,
                token_type="bearer",
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                requires_2fa=False,
                is_totp_enabled=True
            )
        
        # User needs to provide 2FA code -> return challenge with temp token
        temp_token = create_temp_2fa_token(user.id)
        return LoginResponse(
            requires_2fa=True,
            temp_token=temp_token,
            email=user.email,
            full_name=user.full_name,
            is_totp_enabled=True
        )

    # Standard login without 2FA
    token = create_access_token(user.id)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        requires_2fa=False,
        is_totp_enabled=False
    )

@router.post("/2fa/verify-login", response_model=LoginResponse)
def verify_2fa_login(payload: TOTPLoginRequest, db: Session = Depends(get_db)):
    user_id = decode_temp_2fa_token(payload.temp_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA session expired. Please sign in again."
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_totp_enabled or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not active for this account."
        )
    
    if not verify_totp_code(user.totp_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 6-digit Google Authenticator code. Please try again."
        )
    
    token = create_access_token(user.id)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        requires_2fa=False,
        is_totp_enabled=True
    )

# Google Authenticator Setup & Management
@router.get("/2fa/setup", response_model=TOTPSetupResponse)
def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    secret = generate_totp_secret()
    otpauth_url = get_totp_uri(secret, current_user.email, issuer="LinkMind AI")
    qr_code_data = generate_qr_code_base64(otpauth_url)

    current_user.totp_temp_secret = secret
    db.commit()

    return TOTPSetupResponse(
        secret=secret,
        otpauth_url=otpauth_url,
        qr_code=qr_code_data
    )

@router.post("/2fa/enable")
def enable_2fa(
    payload: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.totp_temp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending Google Authenticator setup found. Request a setup QR code first."
        )
    
    if not verify_totp_code(current_user.totp_temp_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check Google Authenticator and try again."
        )
    
    current_user.totp_secret = current_user.totp_temp_secret
    current_user.totp_temp_secret = None
    current_user.is_totp_enabled = True
    db.commit()

    return {
        "success": True,
        "message": "Google Authenticator two-factor authentication enabled successfully."
    }

@router.post("/2fa/disable")
def disable_2fa(
    payload: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_totp_enabled or not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not currently enabled."
        )
    
    if not verify_totp_code(current_user.totp_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code. Please enter the current code from Google Authenticator to disable."
        )
    
    current_user.totp_secret = None
    current_user.totp_temp_secret = None
    current_user.is_totp_enabled = False
    db.commit()

    return {
        "success": True,
        "message": "Google Authenticator two-factor authentication has been disabled."
    }

@router.get("/2fa/status", response_model=TOTPStatusResponse)
def get_2fa_status(current_user: User = Depends(get_current_user)):
    return TOTPStatusResponse(
        is_totp_enabled=bool(current_user.is_totp_enabled),
        email=current_user.email
    )

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
