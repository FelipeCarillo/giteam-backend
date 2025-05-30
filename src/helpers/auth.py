from fastapi import HTTPException, status, Depends, Header
from fastapi.security import OAuth2AuthorizationCodeBearer

from entities import User
from models import User as UserORM

from infra.database import Database
from infra.api_github import APIGithub

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="http://localhost:8000/api/auth/login/github",
    tokenUrl="http://localhost:8000/api/auth/token",
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await APIGithub.get_user_info(token)

    db = Database()
    session = db.get_session()

    user_orm: UserORM = session.query(UserORM).filter(
        UserORM.deleted == False and
        UserORM.provider_id == str(user['id'])
    ).first()

    if user_orm is None:
        raise credentials_exception

    user = User(
        id=user_orm.provider_id,
        provider=user_orm.provider,
        name=user_orm.name,
        username=user['login'],
        email=user_orm.email,
        avatar_url=user['avatar_url'],
        created_at=user_orm.created_at,
        updated_at=user_orm.updated_at,
        settings={**user_orm.settings.__dict__} if user_orm.settings else None,
    )

    db.close_session()

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
