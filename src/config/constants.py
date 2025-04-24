from pydantic import BaseModel


class Constants(BaseModel):
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day


constants = Constants()
