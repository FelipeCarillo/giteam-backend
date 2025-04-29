import logging
from starlette.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Depends, status

from infra.database import Database

from entities.entities import User
from models.models import User as UserORM, UserSettings as UserSettingsORM, ProviderSecretKey as ProviderSecretKeyORM

from schemas.http import ResponseModel
from schemas.user import MeResponse, UpdateUserRequest, ProviderSecretKeySchema, ProviderSecretKeyResponse, \
    DeleteProviderSecretKeyRequest

from helpers.errors import DatabaseError
from helpers.auth import get_current_active_user

logger = logging.getLogger(__name__)

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@user_router.get("/", status_code=status.HTTP_200_OK, response_model=MeResponse)
async def get_user(
        current_user: User = Depends(get_current_active_user),
):
    """Get current user information."""
    return MeResponse(
        message="User information retrieved successfully.",
        user=current_user
    )


@user_router.delete("/", status_code=status.HTTP_200_OK, response_model=ResponseModel)
async def delete_user(
        current_user: User = Depends(get_current_active_user),
):
    """Delete current user."""
    session = None
    try:
        db = Database()
        session = db.get_session()

        user_orm: UserORM = session.query(UserORM).filter(UserORM.id == current_user.id).first()
        if not user_orm:
            raise HTTPException(status_code=404, detail="User not found")

        user_orm.deleted = True

        session.commit()

        return ResponseModel(message="User deleted successfully.")

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException as e:
        logger.error(f"HTTP exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if session:
            session.rollback()
            session.close()


@user_router.put("/", status_code=status.HTTP_200_OK, response_model=ResponseModel)
async def update_user(
        body: UpdateUserRequest,
        current_user: User = Depends(get_current_active_user),
):
    """Update user information."""
    session = None
    try:
        db = Database()
        session = db.get_session()

        user_orm: UserORM = session.query(UserORM).filter(UserORM.id == current_user.id).first()
        if not user_orm:
            raise HTTPException(status_code=404, detail="User not found")

        user_orm.name = body.user.model_dump(exclude_unset=True).get("name")

        user_settings_orm: UserSettingsORM = session.query(UserSettingsORM).filter(
            UserSettingsORM.user_id == current_user.id).first()
        if not user_settings_orm:
            raise HTTPException(status_code=404, detail="User settings not found")

        user_settings = body.user_settings.model_dump(exclude_unset=True)
        for key, value in user_settings.items():
            if key in UserSettingsORM.__dict__.keys():
                setattr(user_settings_orm, key, value)
            else:
                raise HTTPException(status_code=400, detail=f"Invalid field: {key}")

        session.commit()

        return ResponseModel(message="User updated successfully.")

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException as e:
        logger.error(f"HTTP exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if session:
            session.rollback()
            session.close()


@user_router.post("/provider/secret-key", status_code=status.HTTP_201_CREATED, response_model=ResponseModel)
async def create_secret_key(
        body: ProviderSecretKeySchema,
        current_user: User = Depends(get_current_active_user),
):
    """Create a new secret key for the user."""
    session = None
    try:
        db = Database()
        session = db.get_session()

        existing_secret_key = session.query(ProviderSecretKeyORM).filter(
            ProviderSecretKeyORM.provider == body.provider,
            ProviderSecretKeyORM.created_by_id == current_user.id
        ).first()
        if existing_secret_key:
            raise HTTPException(status_code=400, detail="Secret key already exists for this provider.")

        secret_key_orm = ProviderSecretKeyORM(
            provider=body.provider,
            secret_key=body.secret_key,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )

        session.add(secret_key_orm)
        session.commit()

        return ProviderSecretKeyResponse(
            message="Secret key created successfully.",
            provider_secret_key=[ProviderSecretKeySchema(**secret_key_orm.__dict__)]
        )

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException as e:
        logger.error(f"HTTP exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error creating secret key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if session:
            session.rollback()
            session.close()


@user_router.get("/provider/secret-key", status_code=status.HTTP_200_OK, response_model=ProviderSecretKeyResponse)
async def get_secret_keys(
        current_user: User = Depends(get_current_active_user),
):
    """Get all secret keys for the user."""
    session = None
    try:
        db = Database()
        session = db.get_session()

        secret_keys = session.query(ProviderSecretKeyORM).filter(
            ProviderSecretKeyORM.created_by_id == current_user.id
        ).all()

        if not secret_keys:
            return JSONResponse(status_code=204, content={"message": "No secret keys found."})

        secret_keys_list = [ProviderSecretKeySchema(**secret_key.__dict__) for secret_key in secret_keys]

        return ProviderSecretKeyResponse(
            message="Secret keys retrieved successfully.",
            provider_secret_key=secret_keys_list
        )

    except HTTPException as e:
        logger.error(f"HTTP exception: {e.detail}")
        raise e
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error retrieving secret keys: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if session:
            session.rollback()
            session.close()


@user_router.delete("/provider/secret-key", status_code=status.HTTP_200_OK, response_model=ResponseModel)
async def delete_secret_key(
        body: DeleteProviderSecretKeyRequest,
        current_user: User = Depends(get_current_active_user),
):
    """Delete a secret key for the user."""
    session = None
    try:
        db = Database()
        session = db.get_session()

        secret_key_orm: ProviderSecretKeyORM = session.query(ProviderSecretKeyORM).filter(
            ProviderSecretKeyORM.provider == body.provider,
            ProviderSecretKeyORM.created_by_id == current_user.id
        ).first()
        if not secret_key_orm:
            raise HTTPException(status_code=404, detail="Secret key not found")

        session.delete(secret_key_orm)
        session.commit()

        return ResponseModel(message="Secret key deleted successfully.")

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException as e:
        logger.error(f"HTTP exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error deleting secret key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if session:
            session.rollback()
            session.close()


@user_router.put("/provider/secret-key", status_code=status.HTTP_200_OK, response_model=ProviderSecretKeyResponse)
async def update_secret_key(
        body: ProviderSecretKeySchema,
        current_user: User = Depends(get_current_active_user),
):
    """Update a secret key for the user."""
    session = None
    try:
        db = Database()
        session = db.get_session()

        secret_key_orm: ProviderSecretKeyORM = session.query(ProviderSecretKeyORM).filter(
            ProviderSecretKeyORM.provider == body.provider,
            ProviderSecretKeyORM.created_by_id == current_user.id
        ).first()
        if not secret_key_orm:
            raise HTTPException(status_code=404, detail="Secret key not found")

        secret_key_orm.secret_key = body.secret_key

        session.commit()

        return ProviderSecretKeyResponse(
            message="Secret key updated successfully.",
            provider_secret_key=[ProviderSecretKeySchema(**secret_key_orm.__dict__)]
        )

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException as e:
        logger.error(f"HTTP exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error updating secret key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if session:
            session.rollback()
            session.close()
