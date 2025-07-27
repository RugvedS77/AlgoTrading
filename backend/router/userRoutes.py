from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.user_model import User
from database import postgresConn
from schemas.user_schema import UserSchema, ShowUser
from authentication import hashing, oauth2

get_db = postgresConn.get_db
router = APIRouter(
    tags=["User"]
)

@router.get("/user", response_model=List[ShowUser])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    
    users = db.query(User).all()

    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail="No users found")

    return users

@router.get("/user/{user_id}", response_model=ShowUser)
def get_user(user_id : int,db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User Not Found")
    
    return user

@router.post("/user", response_model=ShowUser)
def create_user(req:UserSchema, db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    try:
        new_user = User(
            username=req.username,
            email=req.email,
            password=hashing.Hash.bcrypt(req.password),
            created_at=req.created_at
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f" User created successfully: {new_user}")
    except Exception as e:
        db.rollback()
        print(f" Error creating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail="Error creating user")

    return new_user

@router.put("/user/{user_id}", response_model=ShowUser)
def update_user(req: UserSchema, user_id: int, db :Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    try: 
        user_data = req.model_dump()  # Convert Pydantic model to dict
        updated_user = db.query(User).filter(User.id == user_id).update(user_data)

        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                 detail="User not found")
        
        db.commit()
        user = db.query(User).get(user_id)

        print(f"User updated successfully: {user}")
        return user
    except Exception as e:
        db.rollback()
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail="Error updating user")
    
@router.delete("/user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    user = db.query(User).filter(User.id == user_id).delete(synchronize_session=False)

    # user = db.query(User).get(user_id)
    if not user:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User Not Found")  
     
    db.commit()
    return {"detail": f"User with user id {user_id} deleted successfully"}