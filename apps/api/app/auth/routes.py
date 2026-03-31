from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from app.auth.graph import get_calendar_events
from app.auth.graph import get_graph_token
import os
import httpx
import urllib.parse

router = APIRouter()

@router.get("/auth/request-consent")
def request_consent():
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    redirect_uri = urllib.parse.quote(os.getenv("REDIRECT_URI"), safe="")

    url = (
        f"https://login.microsoftonline.com/{tenant_id}/v2.0/adminconsent"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=https://graph.microsoft.com/.default"
        f"&state=12345"
    )

    return RedirectResponse(url)


@router.get("/debug/group")
async def debug_group():
    group_id = os.getenv("AZURE_GROUP_ID")
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