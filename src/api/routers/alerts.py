import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.api.schemas import AlertCreate, AlertResponse, AlertUpdate
from src.db.models.alert import Alert
from src.db.models.user import User
from src.db.session import get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Alert).filter(Alert.user_id == user.id).all()


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(body: AlertCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = Alert(
        id=uuid.uuid4(),
        user_id=user.id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        **body.model_dump(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = _get_own_alert(db, alert_id, user.id)
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: uuid.UUID, body: AlertUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = _get_own_alert(db, alert_id, user.id)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(alert, field, value)
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = _get_own_alert(db, alert_id, user.id)
    db.delete(alert)
    db.commit()


@router.patch("/{alert_id}/toggle", response_model=AlertResponse)
def toggle_alert(alert_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = _get_own_alert(db, alert_id, user.id)
    alert.is_active = not alert.is_active
    db.commit()
    db.refresh(alert)
    return alert


def _get_own_alert(db: Session, alert_id: uuid.UUID, user_id: uuid.UUID) -> Alert:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
