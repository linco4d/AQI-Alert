from __future__ import annotations
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime, timezone
from .db import SessionLocal, create_all
from .models import Location, Reading
from .config import app_cfg, settings
from .ingest.airnow_provider import AirNowProvider
from .logic.evaluator import evaluate_and_generate_alerts
from .notify.email_notifier import EmailNotifier
from .logic.reporter import build_morning_digest_rows, render_digest_html
from zoneinfo import ZoneInfo


def ensure_seed_locations(db: Session):
    names = {x.name for x in db.query(Location).all()}
    for lc in app_cfg.locations:
        if lc.name not in names:
            db.add(Location(name=lc.name, lat=lc.lat, lon=lc.lon, active=True))
    db.commit()

def ingest_once(db: Session):
    provider = AirNowProvider()
    for loc in db.query(Location).filter_by(active=True).all():
        dtos = provider.fetch_by_location(loc.lat, loc.lon)
        for dto in dtos:
            # Upsert-like: rely on unique constraint to skip dupes
            r = Reading(
                location_id=loc.id,
                provider=dto.provider,
                observed_at=dto.observed_at,
                pm25_ugm3=float(dto.pm25_ugm3),
                aqi=dto.aqi,
                raw_payload=None
            )
            try:
                db.add(r)
                db.commit()
            except Exception as e:
                db.rollback()  # likely a unique violation → skip
    logger.info("Ingest complete.")

def evaluate_and_notify(db: Session):
    alerts = evaluate_and_generate_alerts(db, tz_str="America/Los_Angeles")
    if not alerts:
        return
    notifier = EmailNotifier()
    for a in alerts:
        loc = db.query(Location).get(a.location_id)
        subject = f"[AQI Alert] {loc.name}: PM2.5 {a.observed_value:.1f} µg/m³ ≥ {a.threshold_value:.0f}"
        body = (
            f"Location: {loc.name}\n"
            f"Observed PM2.5: {a.observed_value:.1f} µg/m³\n"
            f"Threshold: {a.threshold_value:.0f} µg/m³\n"
            f"Time (UTC): {datetime.now(timezone.utc).isoformat()}\n"
            f"Provider: AirNow\n"
        )
        notifier.send(subject, body, settings.email_to)

def run_once():
    create_all()
    with SessionLocal() as db:
        ensure_seed_locations(db)
        ingest_once(db)
        #evaluate_and_notify(db)

def send_morning_digest():
    create_all()
    with SessionLocal() as db:
        ensure_seed_locations(db)
        rows = build_morning_digest_rows(db, settings.default_threshold_pm25)
        if not rows:
            logger.info("Morning digest: no rows to send.")
            return
        html = render_digest_html(rows, settings.default_threshold_pm25, tz_str="America/Los_Angeles")
        subject = "[AQI Morning Digest] Air Quality Overview"
        EmailNotifier().send(subject, html, settings.email_to, content_type="html")
        logger.info("Morning digest sent.")

