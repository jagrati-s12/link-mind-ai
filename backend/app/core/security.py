from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import base64
import io
import bcrypt
import jwt
import pyotp
import qrcode
from app.core.config import settings

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "scope": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_temp_2fa_token(subject: str | Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode = {"exp": expire, "sub": str(subject), "scope": "2fa_pending"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded
    except Exception:
        return None

def decode_temp_2fa_token(token: str) -> Optional[int]:
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded.get("scope") != "2fa_pending":
            return None
        return int(decoded.get("sub"))
    except Exception:
        return None

# Google Authenticator (TOTP) Helpers
def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(secret: str, email: str, issuer: str = "LinkMind AI") -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)

def generate_qr_code_base64(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    base64_encoded = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/png;base64,{base64_encoded}"

def verify_totp_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    # Clean code: remove spaces or dashes
    cleaned_code = code.replace(" ", "").replace("-", "").strip()
    totp = pyotp.TOTP(secret)
    # valid_window=1 allows 1 step before or after (30s tolerance)
    return totp.verify(cleaned_code, valid_window=1)
