from __future__ import annotations
import os, yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
load_dotenv()


class LocationCfg(BaseModel):
    name: str
    lat: float
    lon: float
    threshold_pm25: float | None = None

class NotifyCfg(BaseModel):
    channels: List[str] = Field(default_factory=lambda: ["email"])

class QuietHoursCfg(BaseModel):
    start: str = "22:00"
    end: str = "07:00"

class AppCfg(BaseModel):
    poll_interval_minutes: int = 60
    locations: List[LocationCfg]
    notify: NotifyCfg = NotifyCfg()
    dedupe_minutes: int = 180
    quiet_hours: QuietHoursCfg = QuietHoursCfg()

class Settings(BaseModel):
    provider: str = os.getenv("PROVIDER", "airnow")
    airnow_api_key: Optional[str] = os.getenv("AIRNOW_API_KEY")
    db_url: str = os.getenv("DB_URL", "sqlite:///aqi.db")
    default_threshold_pm25: float = float(os.getenv("ALERT_DEFAULT_THRESHOLD_PM25", "35"))
    quiet_start: str = os.getenv("QUIET_HOURS_START", "22:00")
    quiet_end: str = os.getenv("QUIET_HOURS_END", "07:00")
    dedupe_minutes: int = int(os.getenv("DEDUPE_MINUTES", "180"))

    email_enabled: bool = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    email_host: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    email_port: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    email_user: Optional[str] = os.getenv("EMAIL_USERNAME")
    email_pass: Optional[str] = os.getenv("EMAIL_PASSWORD")
    email_from: str = os.getenv("EMAIL_FROM", "alerts@wildfire.local")
    email_to: List[str] = [x.strip() for x in os.getenv("EMAIL_TO", "").split(",") if x.strip()]

def load_app_config(path: str | Path = "config.yaml") -> AppCfg:
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    return AppCfg(**data)

settings = Settings()
app_cfg = load_app_config()
