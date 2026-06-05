import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
    return templates.TemplateResponse(request, "admin/index.html", {
        "user_count": db.query(User).count(),
        "alert_count": db.query(Alert).count(),
        "event_count": db.query(MatchedEvent).count(),
    })


@router.get("/alerts", response_class=HTMLResponse)
def admin_alerts(
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    users = db.query(User).all()
    return templates.TemplateResponse(request, "admin/alerts.html", {
        "alerts": alerts,
        "users": users,
    })


@router.post("/alerts/create")
def admin_create_alert(
    name: str = Form(...),
    keywords: str = Form(""),
    topic: str = Form(""),
    use_llm: str = Form("off"),
    threshold: float = Form(0.7),
    user_id: str = Form(...),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    alert = Alert(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        name=name,
        keywords=keyword_list,
        topic=topic or None,
        use_llm=(use_llm == "on"),
        threshold=threshold,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(alert)
    db.commit()
    return RedirectResponse(url="/admin/alerts", status_code=303)


@router.get("/alerts/{alert_id}/edit", response_class=HTMLResponse)
def admin_edit_alert_form(
    alert_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    alert = db.get(Alert, alert_id)
    if not alert:
        return RedirectResponse(url="/admin/alerts", status_code=303)
    return templates.TemplateResponse(request, "admin/alert_edit.html", {"alert": alert})


@router.post("/alerts/{alert_id}/edit")
def admin_update_alert(
    alert_id: uuid.UUID,
    name: str = Form(...),
    keywords: str = Form(""),
    topic: str = Form(""),
    use_llm: str = Form("off"),
    threshold: float = Form(0.7),
    is_active: str = Form("off"),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    alert = db.get(Alert, alert_id)
    if alert:
        alert.name = name
        alert.keywords = [k.strip() for k in keywords.split(",") if k.strip()]
        alert.topic = topic or None
        alert.use_llm = (use_llm == "on")
        alert.threshold = threshold
        alert.is_active = (is_active == "on")
        db.commit()
    return RedirectResponse(url="/admin/alerts", status_code=303)


@router.post("/alerts/{alert_id}/delete")
def admin_delete_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    alert = db.get(Alert, alert_id)
    if alert:
        db.delete(alert)
        db.commit()
    return RedirectResponse(url="/admin/alerts", status_code=303)


@router.get("/events", response_class=HTMLResponse)
def admin_events(
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_basic_auth),
):
    events = db.query(MatchedEvent).order_by(MatchedEvent.matched_at.desc()).limit(100).all()
    return templates.TemplateResponse(request, "admin/events.html", {"events": events})
