from datetime import datetime as dt
from datetime import timezone as tz

import holoviews as hv
import panel as pn
from dateutil.rrule import MONTHLY, rrule


def month_range():
    """Get a list of months."""
    daterange = list(
        rrule(
            MONTHLY,
            dtstart=dt(2023, 11, 1, 0, 0, tzinfo=tz.utc),
            until=dt.now(tz.utc),
        ),
    )
    return daterange
