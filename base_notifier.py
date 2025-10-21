from __future__ import annotations
from typing import List

class BaseNotifier:
    def send(self, subject: str, body: str, recipients: List[str]) -> None:
        raise NotImplementedError
