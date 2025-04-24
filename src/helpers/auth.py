from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer

from infra.database import Database
from infra.api_github import APIGithub
from models.models import User as UserORM
from entities.entities import User as UserEntity

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="http://localhost:8000/api/auth/login/github",
    tokenUrl="http://localhost:8000/api/auth/token",
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserEntity:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await APIGithub.get_user_info(token)

    db = Database()
    session = db.get_session()

    user_orm = session.query(UserORM).filter(UserORM.provider_id == str(user['id'])).first()
    db.close_session()

    if user_orm is None:
        raise credentials_exception

    user = UserEntity(**user_orm.__dict__)
    return user


async def get_current_active_user(current_user: UserEntity = Depends(get_current_user)) -> UserEntity:
    return current_user
