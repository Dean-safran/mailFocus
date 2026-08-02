from datetime import datetime, timezone
from zoneinfo import ZoneInfo


USER_TIMEZONE = ZoneInfo("America/New_York")


# OVERALL FLOW
# =============
"""

Stored datetime
      ↓
ensure_utc()
      ↓
Timezone-aware UTC datetime
      ↓
Either:
  format_relative_time() → "2 hours ago"
or
  format_local_time()    → "August 1, 2026 at 8:30 PM EDT"

"""


def ensure_utc(value):
    """Return a timezone-aware UTC datetime."""
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def format_relative_time(value):
    """Convert a datetime into text such as '2 hours ago'."""
    utc_value = ensure_utc(value)

    if utc_value is None:
        return "Unknown time"

    difference = datetime.now(timezone.utc) - utc_value
    seconds = max(0, int(difference.total_seconds()))

    if seconds < 60:
        return "Just now"

    minutes = seconds // 60

    if minutes < 60:
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit} ago"

    hours = minutes // 60

    if hours < 24:
        unit = "hour" if hours == 1 else "hours"
        return f"{hours} {unit} ago"

    days = hours // 24

    if days < 7:
        unit = "day" if days == 1 else "days"
        return f"{days} {unit} ago"

    weeks = days // 7

    if weeks < 5:
        unit = "week" if weeks == 1 else "weeks"
        return f"{weeks} {unit} ago"

    return utc_value.astimezone(USER_TIMEZONE).strftime("%B %-d, %Y")


def format_local_time(value):
    """Convert a stored UTC datetime into the user's local timezone."""
    utc_value = ensure_utc(value)

    if utc_value is None:
        return "Unknown time"

    local_value = utc_value.astimezone(USER_TIMEZONE)

    return local_value.strftime(
        # B=month, -d=day without leading 0's, Y=year, 
        # -I=12 hr clock without leading zero,
        # M=minutes, p=AM or PM, Z=timezone abbreviation(EDT or EST)
        "%B %-d, %Y at %-I:%M %p %Z"
    )