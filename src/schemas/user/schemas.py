from typing import Optional, List
from pydantic import BaseModel

from entities.entities import User
from helpers.enums import AIModelProvider
from schemas.http import ResponseModel


class MeResponse(ResponseModel):
    user: User


class UpdateUserSchema(BaseModel):
    name: Optional[str]


class UpdateUserSettingsSchema(BaseModel):
    email_notifications: Optional[bool]
    telegram_notifications: Optional[bool]
    telegram_chat_id: Optional[str]
    daily_limit: Optional[float]
    weekly_limit: Optional[float]
    monthly_limit: Optional[float]
    daily_limit_action: Optional[str]
    weekly_limit_action: Optional[str]
    monthly_limit_action: Optional[str]


class UpdateUserRequest(BaseModel):
    user: UpdateUserSchema
    user_settings: UpdateUserSettingsSchema


class ProviderSecretKeySchema(BaseModel):
    provider: AIModelProvider
    secret_key: str


class ProviderSecretKeyResponse(ResponseModel):
    provider_secret_key: List[ProviderSecretKeySchema]


class DeleteProviderSecretKeyRequest(BaseModel):
    provider: AIModelProvider
