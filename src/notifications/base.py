from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def send(self, subject: str, body: str) -> bool: ...
