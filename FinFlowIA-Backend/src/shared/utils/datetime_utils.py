from datetime import UTC, date, datetime


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    """Format a date object to string."""
    return d.strftime(fmt)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    """Format a datetime object to ISO 8601 string."""
    return dt.strftime(fmt)


def start_of_month(d: date | None = None) -> date:
    """Return the first day of the given date's month."""
    target = d or date.today()
    return target.replace(day=1)


def end_of_month(d: date | None = None) -> date:
    """Return the last day of the given date's month."""
    import calendar

    target = d or date.today()
    last_day = calendar.monthrange(target.year, target.month)[1]
    return target.replace(day=last_day)
