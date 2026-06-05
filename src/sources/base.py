from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    title: str
    description: str = ""
    url: str = ""
    published_at: datetime
    source: str = ""


class EventSource(ABC):
    @abstractmethod
    def fetch(self) -> list[Event]: ...
