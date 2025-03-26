import logging

from core.env import AUTH_ENV
from core.schemas.http import HttpResponse

logger = logging.getLogger()


class Service:

    @staticmethod
    def login() -> str:
        logger.info("Generating Github login URL")
        print("Github: " + AUTH_ENV.GITHUB_LOGIN_URL)

        login_url = f"{AUTH_ENV.GITHUB_LOGIN_URL}?client_id={AUTH_ENV.GITHUB_CLIENT_ID}&redirect_uri={AUTH_ENV.GITHUB_REDIRECT_URI}&scope=user,repo"
        return login_url


def lambda_handler(event, context):
    try:
        logger.info(f"Event: {event}")
        login_url = Service.login()
        logger.info(f"Redirecting to Github login page: {login_url}")
        return HttpResponse.redirect(
            "Redirecting to Github login page",
            headers={"Location": login_url}
        )
    except Exception as e:
        logger.exception(e)
        return HttpResponse.internal_server_error(str(e))
