from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from database import postgresConn
from authentication import hashing, token
from models import user_model

get_db = postgresConn.get_db

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/login")
def login(req: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Fetch user from database
    user = db.query(user_model.User).filter(user_model.User.username == req.username).first()

    # ✅ Check if user exists before accessing password
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist... Try Signing Up"
        )

    print("user got", user.password)  # safe now

    # Verify password
    if not hashing.Hash.verify(req.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )

    # Create access token
    access_token = token.create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}
