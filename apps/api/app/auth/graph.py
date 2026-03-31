import httpx
import os

async def get_graph_token():
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")

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


async def get_calendar_events():
    group_id = os.getenv("AZURE_GROUP_ID")  # <-- use .env here
    token = await get_graph_token()
    access_token = token["access_token"]

    url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/calendar/events"

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