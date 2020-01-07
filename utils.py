from datetime import datetime, timezone


def parse_datetime(v: str) -> datetime:
    tz = None
    if v.endswith(('z', 'Z')):
        tz = timezone.utc
        v = v[:-1]
    dt = datetime.fromisoformat(v)
    if tz:
        dt = dt.replace(tzinfo=tz)
    return dt


class TomlError(ValueError):
    pass
