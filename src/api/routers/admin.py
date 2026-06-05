from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.api.deps import require_admin_basic_auth
from src.db.models.alert import Alert
from src.db.models.matched_event import MatchedEvent
from src.db.models.user import User
from src.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse)
def admin_index(
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    return templates.TemplateResponse(
        "admin/index.html",
        {
            "request": request,
            "user_count": db.query(User).count(),
            "alert_count": db.query(Alert).count(),
            "event_count": db.query(MatchedEvent).count(),
        },
    )


@router.get("/alerts", response_class=HTMLResponse)
def admin_alerts(
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    return templates.TemplateResponse("admin/alerts.html", {"request": request, "alerts": alerts})


@router.get("/events", response_class=HTMLResponse)
def admin_events(
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    events = db.query(MatchedEvent).order_by(MatchedEvent.matched_at.desc()).limit(100).all()
    return templates.TemplateResponse("admin/events.html", {"request": request, "events": events})
