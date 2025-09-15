# backend/router/explainerRoutes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.postgresConn import get_db
from agents.explainerAgent import ExplainerAgent


router = APIRouter(prefix="/explainer", tags=["Explainer"])

@router.get("/results")
def get_explanations(db: Session = Depends(get_db)):
    """
    Fetch all agent results from Postgres and return
    LLM-generated explanations for each one.
    """
    agent = ExplainerAgent(db)
    return {"explanations": agent.explain_all()}

