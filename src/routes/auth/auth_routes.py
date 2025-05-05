from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import status, APIRouter, Request, Form

from config.env import env
from infra.database import Database
from helpers.enums import AuthProvider
from infra.api_github import APIGithub
from models import User as UserORM, UserSettings as UserSettingsORM

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@auth_router.get("/login/github")
async def login_github(request: Request):
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={env.GITHUB_CLIENT_ID}&"
        f"redirect_uri={env.GITHUB_REDIRECT_URI}&scope={env.GITHUB_SCOPE}&state={request.query_params.get('state')}",
        status_code=302
    )


@auth_router.get("/callback/github")
async def callback(
        code: str,
        state: str,
):
    try:
        access_token = await APIGithub.get_access_token(code, env.GITHUB_REDIRECT_URI)

        github_user = await APIGithub.get_user_info(access_token)

        db = Database()
        session = db.get_session()

        user_orm = session.query(UserORM).filter(UserORM.provider_id == str(github_user["id"])).first()

        if user_orm is None:
            email = await APIGithub.get_user_primary_email(access_token)

            user_orm = UserORM(
                name=github_user["name"],
                email=email,
                provider=AuthProvider.GITHUB,
                provider_id=github_user["id"],
            )
            session.add(user_orm)
            session.commit()
            session.refresh(user_orm)

            user_settings_orm = UserSettingsORM(
                user_id=user_orm.id,
                telegram_chat_id=None,
            )
            session.add(user_settings_orm)
            session.commit()

        db.close_session()

        if not env.FRONTEND_URL:
            return RedirectResponse(
                f"/api/docs/oauth2-redirect?code={access_token}&state={state}",
                status_code=302
            )

        return RedirectResponse(
            f"{env.FRONTEND_URL}/auth/callback?code={access_token}",
            status_code=302
        )

    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)})


@auth_router.post("/token")
async def get_token_for_docs(
        code: str = Form(...),
):
    print(code)
    return {"access_token": code, "token_type": "bearer"}
