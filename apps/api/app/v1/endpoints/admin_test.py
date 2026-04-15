from fastapi import APIRouter, Depends

from app.core.deps import build_staff_session_payload, get_current_staff

router = APIRouter()

@router.get("/admin/whoami")
def whoami(staff=Depends(get_current_staff)):
    return build_staff_session_payload(staff)
