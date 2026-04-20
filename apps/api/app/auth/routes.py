from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from app.auth.graph import get_calendar_events
from app.auth.graph import get_graph_token
from app.core.config import get_settings
import os
import httpx
import urllib.parse

router = APIRouter()
settings = get_settings()


def _required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise HTTPException(status_code=500, detail=f"Missing required environment variable: {name}")
    return value


@router.get("/auth/request-consent")
def request_consent():
    tenant_id = _required_env("AZURE_TENANT_ID")
    client_id = _required_env("AZURE_CLIENT_ID")
    redirect_uri = urllib.parse.quote(_required_env("REDIRECT_URI"), safe="")

    url = (
        f"https://login.microsoftonline.com/{tenant_id}/v2.0/adminconsent"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=https://graph.microsoft.com/.default"
        f"&state=12345"
    )

    return RedirectResponse(url)


if settings.enable_debug_routes:
    @router.get("/debug/group")
    async def debug_group():
        group_id = _required_env("AZURE_GROUP_ID")
        token = await get_graph_token()
        access_token = token["access_token"]

        url = f"https://graph.microsoft.com/v1.0/groups/{group_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.json()

@router.get("/calendar/{group_id}")
async def calendar(group_id: str):
    return await get_calendar_events(group_id)

@router.get("/auth/consent-complete")
def consent_complete(admin_consent: str = None, tenant: str = None, state: str = None):
    if admin_consent == "True":
        return {"status": "success", "message": "Admin consent granted", "tenant": tenant}
    else:
        return {"status": "failed", "message": "Admin consent not granted"}
