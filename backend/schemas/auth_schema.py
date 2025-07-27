from pydantic import BaseModel
from typing import Optional

class Login(BaseModel):
    username: str
    password: str

    class Config:

        model_config = {
        "from_attributes": True
        }

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
