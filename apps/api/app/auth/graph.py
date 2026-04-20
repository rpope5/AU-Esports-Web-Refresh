import httpx
import os


def _required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def get_graph_token():
    tenant_id = _required_env("AZURE_TENANT_ID")
    client_id = _required_env("AZURE_CLIENT_ID")
    client_secret = _required_env("AZURE_CLIENT_SECRET")

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        return response.json()


async def get_calendar_events(group_id: str | None = None):
    resolved_group_id = (group_id or os.getenv("AZURE_GROUP_ID") or "").strip()
    if not resolved_group_id:
        raise RuntimeError("Missing AZURE_GROUP_ID for calendar lookups")

    token = await get_graph_token()
    access_token = token["access_token"]

    url = f"https://graph.microsoft.com/v1.0/groups/{resolved_group_id}/calendar/events"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Calendar request failed: {response.status_code} {response.text}"
            )

        return response.json()
