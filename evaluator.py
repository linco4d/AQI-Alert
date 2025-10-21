from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from loguru import logger

from ..models import Reading, Alert, Location
from ..config import settings

def latest_reading_for_location(db: Session, location_id: int) -> Reading | None:
    return db.execute(
        select(Reading).where(Reading.location_id == location_id).order_by(desc(Reading.observed_at)).limit(1)
    ).scalar_one_or_none()

def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)  # treat stored values as UTC
    return dt.astimezone(timezone.utc)

def should_dedupe(db: Session, location_id: int, metric: str, dedupe_minutes: int) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=dedupe_minutes)
    row = db.execute(
        select(Alert).where(Alert.location_id == location_id)
                     .order_by(desc(Alert.created_at))
                     .limit(1)
    ).scalar_one_or_none()
    if not row or row.metric != metric or row.status != "fired":
        return False
    created = _to_utc(row.created_at)
    return created >= cutoff

def evaluate_and_generate_alerts(db: Session, tz_str: str = "America/Los_Angeles") -> list[Alert]:
    fired: list[Alert] = []
    tz = ZoneInfo(tz_str)
    dedupe_min = settings.dedupe_minutes
    for loc in db.query(Location).filter_by(active=True).all():
        latest = latest_reading_for_location(db, loc.id)
        if not latest:
            continue
        threshold = settings.default_threshold_pm25
        obs = latest.pm25_ugm3
        if obs is None:
            continue

        if obs >= threshold:
            # quiet hours check in local time
            now_local = datetime.now(tz)
            from ..logic.normalize import within_quiet_hours
            quiet = within_quiet_hours(now_local, settings.quiet_start, settings.quiet_end)
            dedupe = should_dedupe(db, loc.id, "pm25", dedupe_min)

            status = "fired"
            reason = None
            if dedupe:
                status, reason = "suppressed", "dedupe_window"
            elif quiet:
                status, reason = "suppressed", "quiet_hours"

            alert = Alert(
                location_id=loc.id,
                metric="pm25",
                threshold_value=threshold,
                observed_value=float(obs),
                status=status,
                reason=reason
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            if status == "fired":
                fired.append(alert)
            logger.info(f"Alert {status} for {loc.name}: PM2.5={obs} threshold={threshold} reason={reason}")
    return fired
