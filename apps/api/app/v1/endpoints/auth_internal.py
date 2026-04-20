from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import build_staff_principal, get_db
from app.models.admin_user import AdminUser
from app.schemas.auth_internal import LoginRequest, AuthResponse
from app.core.passwords import verify_password
from app.core.jwt_auth import create_access_token

router = APIRouter()

@router.post("/auth/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    username = data.username.strip()

    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    staff = build_staff_principal(db, user)
    token = create_access_token({"sub": user.username, "role": staff.role})

    return AuthResponse(
        access_token=token,
        role=staff.role,
        username=user.username,
        must_change_password=bool(user.must_change_password),
        allowed_game_slugs=sorted(staff.allowed_game_slugs),
        has_global_game_access=staff.has_global_game_access,
        permissions=staff.permissions.to_dict(),
    )
