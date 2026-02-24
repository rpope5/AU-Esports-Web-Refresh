from fastapi import APIRouter, Depends
from app.core.deps import require_admin

router = APIRouter()

@router.get("/admin/whoami")
def whoami(user=Depends(require_admin)):
    # user contains JWT payload: sub + role
    return {"username": user.get("sub"), "role": user.get("role")}