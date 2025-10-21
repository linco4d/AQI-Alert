from __future__ import annotations
import typer
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta, timezone
from loguru import logger
from .runner import run_once, send_morning_digest
from zoneinfo import ZoneInfo
from .db import create_all, SessionLocal
from .logic.reporter import daily_summary, write_csv

app = typer.Typer(add_completion=False)

@app.command()
def init_db():
    create_all()
    typer.echo("DB initialized and locations seeded on first run.")

@app.command()
def run_once_cmd():
    run_once()

@app.command()
def schedule(minutes: int = 60, delay_seconds: int = 0):
    """
    Hourly: ingest-only (no per-run emails).
    Daily: send 7:05am PT morning digest.
    """
    sched = BlockingScheduler(timezone="America/Los_Angeles")
    from datetime import datetime, timedelta
    # Hourly ingestion job
    start = datetime.now() + timedelta(seconds=delay_seconds)
    sched.add_job(run_once, "interval", minutes=minutes, next_run_time=start)
    # Daily digest at 7:05 AM PT
    sched.add_job(send_morning_digest, "cron", hour=7, minute=5)
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass



@app.command()
def report(date: str = typer.Argument(None)):
    if date:
        y, m, d = map(int, date.split("-"))
        target = datetime(y, m, d, tzinfo=timezone.utc)
    else:
        target = datetime.now(timezone.utc) - timedelta(days=1)
        target = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
    with SessionLocal() as db:
        rows = daily_summary(db, target)
    path = f"reports/{target.date().isoformat()}_summary.csv"
    write_csv(path, rows)
    typer.echo(f"Wrote {path}")

@app.command()
def digest_now():
    """
    Send the Morning Digest email immediately (useful for testing).
    """
    send_morning_digest()

if __name__ == "__main__":
    app()

