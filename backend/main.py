from fastapi import FastAPI, HTTPException, Depends, status

from router import userRoutes, auth

app = FastAPI(
    title = "AlgoTrading API"
)

@app.post("/")
def root():
    return {"data": "Welcome to the root endpoint"}

app.include_router(auth.router)
app.include_router(userRoutes.router)