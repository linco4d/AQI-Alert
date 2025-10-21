from __future__ import annotations
from datetime import time, datetime

def within_quiet_hours(now_local: datetime, start_str: str, end_str: str) -> bool:
    s = time.fromisoformat(start_str)
    e = time.fromisoformat(end_str)
    t = now_local.time()
    if s <= e:
        return s <= t < e
    # wraps midnight
    return t >= s or t < e
