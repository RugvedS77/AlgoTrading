from router import newsRoutes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.postgresConn import create_all_tables
import threading

from router import userRoutes, auth, agentRoutes, accountRoutes, explainerRoutes
from Pred_models.trend_pred_new import TrendPredict

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

def run_predictor_background():
    """
    Creates a predictor instance and runs it forever.
    """
    print("--- 🚀 Starting background predictor thread... ---")
    predictor = TrendPredict()
    # Using shorter sleep time for quick testing. Change to 300 for 5 minutes.
    predictor.run_continuously(sleep_seconds=300)


@app.post("/")
def root():
    return {"data": "Welcome to the root endpoint"}

# init tables
create_all_tables()

predictor_thread = threading.Thread(target=run_predictor_background, daemon=True)
predictor_thread.start()

# Routers
app.include_router(auth.router)
app.include_router(accountRoutes.router)
app.include_router(userRoutes.router)
app.include_router(newsRoutes.router)
app.include_router(agentRoutes.router)
app.include_router(explainerRoutes.router)
