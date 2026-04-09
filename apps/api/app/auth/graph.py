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

        # 🔴 CRITICAL: validate response
        if response.status_code != 200:
            raise RuntimeError(
                f"Token request failed: {response.status_code} {response.text}"
            )

        token_data = response.json()

        # 🔴 CRITICAL: ensure token exists
        access_token = token_data.get("access_token")
        if not access_token:
            raise RuntimeError(f"No access_token in response: {token_data}")

        return access_token


async def get_calendar_events():
    group_id = os.getenv("AZURE_GROUP_ID")
    if not group_id:
        raise RuntimeError("Missing AZURE_GROUP_ID")

    access_token = await get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/calendar/events"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "$select": "subject,start,end",
        "$top": 50
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise RuntimeError(
                f"Calendar request failed: {response.status_code} {response.text}"
            )

        return response.json()