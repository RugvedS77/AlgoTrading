from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.account_schema import AccountSchema, AccountCreate
from typing import List
from pydantic import BaseModel
from typing import Literal
from collections import defaultdict
from models.trade_model import Trade, TradeSide

from models.account_model import Account
from database import postgresConn

get_db = postgresConn.get_db
router = APIRouter(
    tags=["Account"])

class TradeRequest(BaseModel):
    username: str
    ticker: str
    side: Literal["BUY", "SELL"]
    price: float
    quantity: int

# MODIFICATION: The updated_account will no longer contain positions
class TradeResponse(BaseModel):
    message: str
    updated_account: AccountSchema 

# MODIFICATION: Create proper response models for the portfolio endpoint
class PositionSchema(BaseModel):
    ticker: str
    quantity: float
    average_buy_price: float

class PortfolioResponse(BaseModel):
    cash_available: float
    open_positions: List[PositionSchema]

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

# # MODIFICATION: Added the 'response_model' for validation and documentation
# @router.get("/portfolio/{username}", response_model=PortfolioResponse)
# def get_calculated_portfolio(username: str, db: Session = Depends(get_db)):
#     account = db.query(Account).filter(Account.user_name == username).first()
#     if not account:
#         raise HTTPException(status_code=404, detail="Account not found")

#     # The calculation logic here is correct and remains the same
#     positions_map = defaultdict(lambda: {'quantity': 0, 'total_cost': 0})
#     for trade in account.trades: # Use the relationship directly
#         pos = positions_map[trade.ticker]
#         if trade.side == TradeSide.BUY:
#             pos['quantity'] += trade.quantity
#             pos['total_cost'] += trade.quantity * trade.price
#         elif trade.side == TradeSide.SELL:
#             avg_price = pos['total_cost'] / pos['quantity'] if pos['quantity'] > 0 else 0
#             pos['total_cost'] -= trade.quantity * avg_price
#             pos['quantity'] -= trade.quantity

#     open_positions = []
#     for ticker, data in positions_map.items():
#         if data['quantity'] > 0.0001: # Use a small threshold for floating point comparison
#             open_positions.append({
#                 "ticker": ticker,
#                 "quantity": data['quantity'],
#                 "average_buy_price": data['total_cost'] / data['quantity']
#             })

#     return {
#         "cash_available": account.cash_available,
#         "open_positions": open_positions
#     }


# # MODIFICATION: Fully refactored and optimized trade endpoint
# @router.post("/account/trade", response_model=TradeResponse)
# def execute_trade(trade: TradeRequest, db: Session = Depends(get_db)):
#     account = db.query(Account).filter(Account.user_name == trade.username).first()
#     if not account:
#         raise HTTPException(status_code=404, detail="Account not found")

#     if trade.side == "BUY":
#         cost = trade.price * trade.quantity
#         if account.cash_available < cost:
#             raise HTTPException(status_code=400, detail="Not enough cash available")
#         account.cash_available -= cost

#     elif trade.side == "SELL":
#         # OPTIMIZATION: Calculate current shares from the existing relationship, not a new function call
#         current_quantity = 0
#         for t in account.trades:
#             if t.ticker == trade.ticker:
#                 if t.side == TradeSide.BUY:
#                     current_quantity += t.quantity
#                 else:
#                     current_quantity -= t.quantity
        
#         if current_quantity < trade.quantity:
#             raise HTTPException(status_code=400, detail="Not enough shares to sell")
        
#         account.cash_available += trade.price * trade.quantity

#     # Record the new trade
#     new_trade = Trade(
#         ticker=trade.ticker,
#         side=trade.side,
#         quantity=trade.quantity,
#         price=trade.price,
#         account_id=account.id
#     )
#     db.add(new_trade)
#     db.commit()
#     db.refresh(account)

#     return {"message": "Trade recorded successfully", "updated_account": account}
