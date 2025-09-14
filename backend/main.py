from router import newsRoutes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.postgresConn import create_all_tables

from router import userRoutes, auth, agentRoutes, accountRoutes, explainerRoutes

app = FastAPI(
    title="AlgoTrading API"
)

# ✅ Allow frontend (React) to talk with backend
origins = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # use ["*"] to allow all origins (not safe in prod)
    allow_credentials=True,
    allow_methods=["*"],         # allow all HTTP methods
    allow_headers=["*"],         # allow all headers
)

@app.post("/")
def root():
    return {"data": "Welcome to the root endpoint"}

# init tables
create_all_tables()

# Routers
app.include_router(auth.router)
app.include_router(accountRoutes.router)
app.include_router(userRoutes.router)
app.include_router(newsRoutes.router)
app.include_router(agentRoutes.router)
app.include_router(explainerRoutes.router)
