from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routers import alerts, auth, channels, admin
from src.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Alert Notification System", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(channels.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
