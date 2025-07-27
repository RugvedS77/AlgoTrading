from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from schemas import auth_schema
from database import postgresConn
from authentication import hashing, token
from models import user_model

get_db = postgresConn.get_db

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/login")
def login(req: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(user_model.User).filter(user_model.User.username == req.username).first()

    print("user got", user.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User do not exist... Try Signing Up")
    
    if not hashing.Hash.verify(req.password , user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid Credentials")
    
    access_token = token.create_access_token(data={"sub" : user.username})

    return {"access_token": access_token, "token_type": "bearer"}