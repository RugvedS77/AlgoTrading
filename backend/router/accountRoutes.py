from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.account_schema import AccountSchema, AccountCreate
from typing import List

from models.account_model import Account
from database import postgresConn

get_db = postgresConn.get_db
router = APIRouter(
    tags=["Account"])

@router.get("/account", response_model=List[AccountSchema])
def get_all_accounts(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()

    if not accounts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail="No accounts found")

    return accounts

@router.get("/account/{account_id}", response_model=AccountSchema)
def get_account(account_id : int,db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Account Not Found")
    
    return account

@router.post("/account", response_model=AccountSchema)
def create_account(req:AccountCreate, db: Session = Depends(get_db)):
    try:
        new_account = Account(
            user_name=req.user_name,
            total_equity=req.total_equity,
            cash_available=req.cash_available,
            risk_limits=req.risk_limits.model_dump()
        )
        
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        print(f" Account created successfully: {new_account}")
    except Exception as e:
        db.rollback()
        print(f" Error creating account: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail="Error creating account")

    return new_account

@router.put("/account/{account_id}", response_model=AccountSchema)
def update_account(req: AccountCreate, account_id: int, db :Session = Depends(get_db)):
    try:
        account = db.query(Account).filter(Account.id == account_id).first()

        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Account Not Found")

        account.user_name = req.user_name
        account.total_equity = req.total_equity
        account.cash_available = req.cash_available
        account.risk_limits = req.risk_limits.model_dump()

        db.commit()
        db.refresh(account)
        print(f" Account updated successfully: {account}")
    except Exception as e:
        db.rollback()
        print(f" Error updating account: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail="Error updating account")

    return account
def fetch_account(username: str, db: Session) -> dict:
    """
    Fetch portfolio/account details from the database.
    """
    acct = db.query(Account).filter(Account.user_name == username).first()
    if not acct:
        raise ValueError(f"Account for user {username} not found.")

    portfolio = {
        "total_equity": float(acct.total_equity),
        "cash_available": float(acct.cash_available),
        "risk_limits": acct.risk_limits,
        "realized_drawdown_30d_pct": float(acct.realized_drawdown_30d_pct),
        "portfolio_volatility_30d_pct": float(acct.portfolio_volatility_30d_pct),
    }
    return portfolio


@router.get("/account/fetch/{username}", response_model=AccountSchema)
def fetch_account_from_db(username: str, db: Session = Depends(get_db)) -> AccountSchema:
    """
    FastAPI route to fetch account details.
    """
    acct = db.query(Account).filter(Account.user_name == username).first()
    if not acct:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account for user {username} not found.")
    return acct