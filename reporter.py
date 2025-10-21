from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timezone, timedelta
import csv, os
from zoneinfo import ZoneInfo
from ..models import Reading, Location


def daily_summary(db: Session, date_utc: datetime):
    start = datetime(date_utc.year, date_utc.month, date_utc.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    rows = []
    for loc in db.query(Location).filter_by(active=True).all():
        q = (
            db.query(
                func.max(Reading.pm25_ugm3),
                func.avg(Reading.pm25_ugm3)
            )
            .filter(and_(Reading.location_id == loc.id, Reading.observed_at >= start, Reading.observed_at < end))
            .one_or_none()
        )
        if q:
            rows.append((loc.name, float(q[0] or 0), float(q[1] or 0)))
    return rows

def write_csv(path: str, rows: list[tuple[str, float, float]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["location", "max_pm25_ugm3", "avg_pm25_ugm3"])
        for r in rows:
            w.writerow(r)

def latest_reading(db: Session, location_id: int) -> Reading | None:
    return db.execute(
        select(Reading)
        .where(Reading.location_id == location_id)
        .order_by(desc(Reading.observed_at))
        .limit(1)
    ).scalar_one_or_none()

def pm25_category(pm25: float) -> tuple[str, str]:
    """
    Return (category, color_emoji) using simplified EPA-like bands for PM2.5 (µg/m³).
    """
    # Bands (24h concentration) simplified for messaging; you can refine later
    if pm25 <= 12.0:             return ("Good", "🟢")
    if pm25 <= 35.4:             return ("Moderate", "🟡")
    if pm25 <= 55.4:             return ("Unhealthy for Sensitive Groups", "🟠")
    if pm25 <= 150.4:            return ("Unhealthy", "🔴")
    if pm25 <= 250.4:            return ("Very Unhealthy", "🟣")
    return ("Hazardous", "🟤")

def build_morning_digest_rows(db: Session, threshold: float) -> list[dict]:
    ysum = yesterday_summary(db)
    rows = []
    for loc in db.query(Location).filter_by(active=True).all():
        last = latest_reading(db, loc.id)
        if not last or last.pm25_ugm3 is None:
            continue
        pm = float(last.pm25_ugm3)
        cat, badge = pm25_category(pm)
        delta = pm - threshold
        ys = ysum.get(loc.name, {})
        rows.append({
            "city": loc.name,
            "pm25_now": pm,
            "category_now": cat,
            "badge": badge,
            "delta_now": delta,
            "y_max": ys.get("max_pm25"),
            "y_avg": ys.get("avg_pm25"),
        })
    rows.sort(key=lambda r: (r["pm25_now"] if r["pm25_now"] is not None else -1), reverse=True)
    return rows


def render_digest_html(rows: list[dict], threshold: float, tz_str: str = "America/Los_Angeles") -> str:
    now_local = datetime.now(ZoneInfo(tz_str))
    header = f"""
    <html><body>
    <h2 style="font-family:system-ui;margin-bottom:4px;">Daily Air Quality Digest</h2>
    <div style="color:#555;font-family:system-ui;margin-bottom:14px;">
      {now_local:%A, %B %d, %Y • %I:%M %p %Z}
      &nbsp;|&nbsp; Threshold: {threshold:.0f} µg/m³ (PM2.5)
    </div>
    <table cellpadding="8" cellspacing="0" border="0" style="border-collapse:collapse;font-family:system-ui;font-size:14px;">
      <thead>
        <tr style="background:#f1f3f5;">
          <th align="left">City</th>
          <th align="right">Now PM2.5</th>
          <th align="left">Now Category</th>
          <th align="right">Δ vs Thresh</th>
          <th align="right">Yday Max</th>
          <th align="right">Yday Avg</th>
          <th align="left">Status</th>
        </tr>
      </thead>
      <tbody>
    """
    def fmt_val(v):
        return f"{v:.1f}" if v is not None else "—"
    def fmt_delta(d):
        if d is None: return "—"
        sign = "+" if d >= 0 else "–"; mag = abs(d)
        color = "#c92a2a" if d >= 0 else "#2b8a3e"
        return f"<span style='color:{color};font-variant-numeric:tabular-nums;'>{sign}{mag:.1f}</span>"

    body = []
    for r in rows:
        status = "Above" if r["delta_now"] is not None and r["delta_now"] >= 0 else "Below"
        color = "#c92a2a" if status == "Above" else "#2b8a3e"
        body.append(f"""
          <tr style="border-bottom:1px solid #eee;">
            <td>{r['city']}</td>
            <td align="right" style="font-variant-numeric:tabular-nums;">{fmt_val(r['pm25_now'])}</td>
            <td>{r['badge']} {r['category_now']}</td>
            <td align="right">{fmt_delta(r['delta_now'])}</td>
            <td align="right" style="font-variant-numeric:tabular-nums;">{fmt_val(r['y_max'])}</td>
            <td align="right" style="font-variant-numeric:tabular-nums;">{fmt_val(r['y_avg'])}</td>
            <td style="color:{color};">{status}</td>
          </tr>
        """)
    tail = """
      </tbody>
    </table>
    <div style="color:#666;font-size:12px;margin-top:10px;font-family:system-ui;">
      Source: AirNow. “Now” uses most recently ingested PM2.5; “Yday” aggregates cover the previous UTC day.
    </div>
    </body></html>
    """
    return header + "\n".join(body) + tail

    def fmt_delta(d: float) -> str:
        sign = "+" if d >= 0 else "–"
        mag = abs(d)
        color = "#c92a2a" if d >= 0 else "#2b8a3e"
        return f"<span style='color:{color};font-variant-numeric:tabular-nums;'>{sign}{mag:.1f}</span>"

    body_rows = []
    for r in rows:
        status = "Above" if r["delta"] >= 0 else "Below"
        color = "#c92a2a" if status == "Above" else "#2b8a3e"
        body_rows.append(f"""
          <tr style="border-bottom:1px solid #eee;">
            <td>{r['city']}</td>
            <td align="right" style="font-variant-numeric:tabular-nums;">{r['pm25']:.1f}</td>
            <td>{r['badge']} {r['category']}</td>
            <td align="right">{fmt_delta(r['delta'])}</td>
            <td style="color:{color};">{status}</td>
          </tr>
        """)
    tail = """
      </tbody>
    </table>
    <div style="color:#666;font-size:12px;margin-top:10px;font-family:system-ui;">
      Source: AirNow. PM2.5 shown; categories approximate EPA bands.
    </div>
    </body></html>
    """
    return header + "\n".join(body_rows) + tail

def yesterday_summary(db: Session) -> dict[str, dict]:
    # UTC day boundary; digest renders with local tz separately
    today_utc = datetime.now(timezone.utc).date()
    start = datetime(today_utc.year, today_utc.month, today_utc.day, tzinfo=timezone.utc) - timedelta(days=1)
    end = start + timedelta(days=1)

    out: dict[str, dict] = {}
    for loc in db.query(Location).filter_by(active=True).all():
        q = (
            db.query(
                func.max(Reading.pm25_ugm3),
                func.avg(Reading.pm25_ugm3)
            )
            .filter(and_(Reading.location_id == loc.id,
                         Reading.observed_at >= start,
                         Reading.observed_at < end))
            .one_or_none()
        )
        max_pm = float(q[0]) if q and q[0] is not None else None
        avg_pm = float(q[1]) if q and q[1] is not None else None
        out[loc.name] = {"max_pm25": max_pm, "avg_pm25": avg_pm}
    return out
