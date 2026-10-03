"""Explicit IANA logical days. UTC originals and historical timezone identities never change."""
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

OWNER_REFERENCE_TIMEZONE = 'Europe/Warsaw'


def validate_timezone(name: str) -> str:
    if not isinstance(name, str) or not name or len(name) > 100:
        raise ValueError('IANA timezone required')
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError('IANA timezone required') from None
    return name


def logical_day(utc_timestamp: str, timezone_name: str) -> str:
    zone = ZoneInfo(validate_timezone(timezone_name))
    value = datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
    if value.utcoffset() is None or value.utcoffset().total_seconds() != 0:
        raise ValueError('Source UTC required')
    return value.astimezone(zone).date().isoformat()


def day_window(local_date: str, timezone_name: str) -> tuple[str, str]:
    zone = ZoneInfo(validate_timezone(timezone_name))
    day = date.fromisoformat(local_date)
    start = datetime.combine(day, time.min, zone).astimezone(timezone.utc)
    next_midnight = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(timezone.utc)
    return start.isoformat(), (next_midnight - timedelta(microseconds=1)).isoformat()


def scope_key(local_date: str, timezone_name: str) -> str:
    validate_timezone(timezone_name)
    date.fromisoformat(local_date)
    return 'IANA_LOCAL_V1:' + timezone_name + ':' + local_date
