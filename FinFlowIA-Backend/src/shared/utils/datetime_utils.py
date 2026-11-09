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


def add_months(d: date, n: int) -> date:
    """Return the first-of-month date n months after d's month."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def iter_bucket_starts(start: date, end: date, granularity: str) -> list[date]:
    """Enumerate the start date of every bucket between start and end (inclusive)."""
    from datetime import timedelta

    buckets: list[date] = []
    if granularity == "day":
        current = start
        while current <= end:
            buckets.append(current)
            current += timedelta(days=1)
    elif granularity == "month":
        current, last = start.replace(day=1), end.replace(day=1)
        while current <= last:
            buckets.append(current)
            current = add_months(current, 1)
    else:  # "year"
        current, last = start.replace(month=1, day=1), end.replace(month=1, day=1)
        while current <= last:
            buckets.append(current)
            current = current.replace(year=current.year + 1)
    return buckets


def format_bucket_label(d: date, granularity: str) -> str:
    """Format a bucket start date into a chart-friendly label."""
    if granularity == "day":
        return d.isoformat()
    if granularity == "month":
        return d.strftime("%Y-%m")
    return str(d.year)
