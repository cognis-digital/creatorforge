"""Content calendar — turn a pile of ideas into a posting schedule.

Spreads ideas across the week at a chosen cadence, assigning each to a platform
it fits. Dates are explicit (you pass the start date), so the schedule is
reproducible and easy to diff.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional

# preferred weekday slots in fill order (Mon=0 … Sun=6)
_SLOT_ORDER = [0, 2, 4, 1, 3, 5, 6]


def _weekday_slots(per_week: int) -> List[int]:
    per_week = max(1, min(7, per_week))
    return sorted(_SLOT_ORDER[:per_week])


def _as_date(d) -> date:
    if isinstance(d, date):
        return d
    return datetime.strptime(d, "%Y-%m-%d").date()


def build_calendar(ideas: List[dict], start, per_week: int = 3, weeks: int = 4) -> List[dict]:
    if not ideas:
        return []
    start = _as_date(start)
    monday = start - timedelta(days=start.weekday())  # week containing start
    slots = _weekday_slots(per_week)

    schedule: List[dict] = []
    idx = 0
    for w in range(weeks):
        for wd in slots:
            day = monday + timedelta(weeks=w, days=wd)
            if day < start:
                continue
            idea = ideas[idx % len(ideas)]
            idx += 1
            platform = (idea.get("platforms") or ["youtube"])[0]
            schedule.append({
                "date": day.isoformat(),
                "weekday": day.strftime("%A"),
                "title": idea.get("title", ""),
                "format": idea.get("format", ""),
                "platform": platform,
            })
    return schedule
