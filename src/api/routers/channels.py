import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.api.schemas import ChannelCreate, ChannelResponse
from src.db.models.channel import ChannelType, NotificationChannel
from src.db.models.user import User
from src.db.session import get_db

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("/", response_model=list[ChannelResponse])
def list_channels(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(NotificationChannel).filter(NotificationChannel.user_id == user.id).all()


@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
def create_channel(body: ChannelCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.type not in [t.value for t in ChannelType]:
        raise HTTPException(status_code=400, detail=f"Invalid channel type: {body.type}")
    channel = NotificationChannel(
        id=uuid.uuid4(),
        user_id=user.id,
        type=ChannelType(body.type),
        config=body.config,
        is_active=True,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_channel(channel_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.query(NotificationChannel).filter(
        NotificationChannel.id == channel_id,
        NotificationChannel.user_id == user.id,
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    db.delete(channel)
    db.commit()
