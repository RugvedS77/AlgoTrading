from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    password: str
    created_at: datetime

    class Config:

        model_config = {
        "from_attributes": True
        }

class ShowUser(BaseModel):
    id: int
    username: str
    email: str

    class Config:

        model_config = {
        "from_attributes": True
        }