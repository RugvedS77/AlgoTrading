from fastapi import FastAPI, HTTPException, Depends
from typing import List
# from . import model
from models.user_model import User
from schemas.user_schema import UserSchema
from database import postgresConn
from sqlalchemy.orm import Session

# from .router import user_router

get_db = postgresConn.get_db

app = FastAPI(
    title = "AlgoTrading API"
)

@app.post("/")
def root():
    return {"data": "Welcome to the root endpoint"}

@app.get("/user")
def get_all_users(db: Session = Depends(get_db)):
    
    users = db.query(User).all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users

@app.post("/user", response_model=List[UserSchema])
def create_user(req:UserSchema, db: Session = Depends(get_db)):
    try:
        new_user = User(
            username=req.username,
            email=req.email,
            password=req.password,
            created_at=req.created_at
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"✅ User created successfully: {new_user}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")

    return new_user