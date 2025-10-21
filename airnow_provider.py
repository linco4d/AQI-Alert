from __future__ import annotations
import httpx
from datetime import datetime, timezone
from dateutil import parser as dateparser
from tenacity import retry, wait_exponential_jitter, stop_after_attempt
from loguru import logger
from typing import List

from ..config import settings
from .base_provider import BaseProvider, ReadingDTO

AIRNOW_ENDPOINT = "https://www.airnowapi.org/aq/observation/latLong/current"

class AirNowProvider(BaseProvider):
    name = "airnow"

    @retry(wait=wait_exponential_jitter(1, 8), stop=stop_after_attempt(4))
    def fetch_by_location(self, lat: float, lon: float) -> List[ReadingDTO]:
        params = {
            "format": "application/json",
            "latitude": str(lat),
            "longitude": str(lon),
            "distance": "25",  # miles radius
            "API_KEY": settings.airnow_api_key or "",
        }
        r = httpx.get(AIRNOW_ENDPOINT, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        # AirNow returns multiple pollutants; filter for PM2.5
        pm25_rows = [d for d in data if str(d.get("ParameterName", "")).lower() in ("pm2.5", "pm25")]
        out: List[ReadingDTO] = []
        for row in pm25_rows:
            val = row.get("AQI")
            # AirNow sometimes includes Concentration; AQI is not µg/m3. Prefer Concentration if present.
            conc = row.get("Concentration")
            observed = row.get("DateObserved")
            hour = row.get("HourObserved")
            tz = row.get("LocalTimeZone", "UTC")
            # Compose timestamp; treat as local then convert to UTC best-effort
            ts_local = dateparser.parse(f"{observed} {hour:02d}:00:00 {tz}")
            ts_utc = ts_local.astimezone(timezone.utc)
            pm25_ugm3 = float(conc) if conc is not None else float(val or 0)  # fallback; not ideal but workable
            out.append(ReadingDTO(
                observed_at=ts_utc,
                pm25_ugm3=pm25_ugm3,
                aqi=int(val) if val is not None else None,
                provider=self.name
            ))
        logger.info(f"AirNow: {len(out)} PM2.5 rows for lat={lat} lon={lon}")
        return out
