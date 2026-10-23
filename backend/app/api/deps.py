from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import decode_access_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    if not token:
        # Default dev user fallback if no token provided, to allow seamless demo/local exploration
        user = db.query(User).filter(User.email == "demo@linkmind.ai").first()
        if not user:
            from app.core.security import hash_password
            from app.models import UserProfile
            user = User(
                email="demo@linkmind.ai",
                hashed_password=hash_password("password123"),
                full_name="Demo User"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            profile = UserProfile(user_id=user.id, target_roles=["AI Engineer", "Software Engineer"])
            db.add(profile)
            db.commit()
        return user

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or expired session.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
    
    return user
