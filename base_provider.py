from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime

class ReadingDTO(BaseModel):
    observed_at: datetime  # UTC
    pm25_ugm3: float
    aqi: int | None = None
    provider: str

class BaseProvider:
    name: str
    async_mode: bool = False
    def fetch_by_location(self, lat: float, lon: float) -> list[ReadingDTO]:
        raise NotImplementedError
