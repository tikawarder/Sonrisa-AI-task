from fastapi import FastAPI

from src.api.routers import alerts, auth, channels, admin

app = FastAPI(title="Alert Notification System", version="0.1.0")

app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(channels.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
