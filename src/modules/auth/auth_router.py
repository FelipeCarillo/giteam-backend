from fastapi import APIRouter

from routes.login.login import lambda_handler

auth_router = APIRouter(
    prefix="/auth",
    tags=["Routes for Authentication (Github)"]
)


@auth_router.get(
    "/login",
    name="Login Github",
    summary="Redirect URL to Github login page",
    status_code=302,
    response_description="Redirect to Github login page"
)
async def login():
    return lambda_handler({}, {})


@auth_router.get(
    "/callback",
    name="Callback Github",
    summary="Callback URL from Github",
    response_description="Callback from Github"
)
async def callback():
    return {"message": "Callback from Github"}
