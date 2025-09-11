from router import newsRoutes
from fastapi import FastAPI, HTTPException, Depends, status
from database.postgresConn import create_all_tables

from router import userRoutes, auth, agentRoutes, accountRoutes

app = FastAPI(
    title = "AlgoTrading API"
)

@app.post("/")
def root():
    return {"data": "Welcome to the root endpoint"}

create_all_tables()

app.include_router(auth.router)
app.include_router(accountRoutes.router)
app.include_router(userRoutes.router)
app.include_router(newsRoutes.router)
app.include_router(agentRoutes.router)
