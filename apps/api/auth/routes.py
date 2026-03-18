from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import os
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


@router.get("/auth/consent-complete")
def consent_complete(admin_consent: str = None, tenant: str = None, state: str = None):
    if admin_consent == "True":
        return {"status": "success", "message": "Admin consent granted", "tenant": tenant}
    else:
        return {"status": "failed", "message": "Admin consent not granted"}