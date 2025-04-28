import httpx
from pydantic import EmailStr

from config.env import env


class APIGithub:
    @staticmethod
    async def get_access_token(code: str, redirect_uri: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": env.GITHUB_CLIENT_ID,
                        "client_secret": env.GITHUB_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                    headers={"Accept": "application/json"},
                )
                token_response.raise_for_status()

                token_data = token_response.json()

                return token_data["access_token"]

        except httpx.RequestError as e:
            raise Exception(f"Error getting access token: {e}")

    @staticmethod
    async def get_user_info(token: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token}"},
                )
                user_response.raise_for_status()

                github_user = user_response.json()

                return github_user

        except httpx.RequestError as e:
            raise Exception(f"Error getting user info: {e}")

    @staticmethod
    async def get_user_primary_email(token: str) -> EmailStr:
        try:
            async with httpx.AsyncClient() as client:
                emails_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"token {token}"},
                )
                emails_response.raise_for_status()

                emails = emails_response.json()
                primary_email = next((email["email"] for email in emails if email["primary"]), None)

                return primary_email

        except httpx.RequestError as e:
            raise Exception(f"Error getting user emails: {e}")
