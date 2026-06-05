from src.db.base import Base
from src.db.session import engine
from src.db.models import User, Alert, NotificationChannel, MatchedEvent, NotificationLog  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created.")
