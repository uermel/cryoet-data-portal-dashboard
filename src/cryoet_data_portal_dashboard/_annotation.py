from datetime import datetime as dt
from datetime import timezone as tz

import panel as pn
from cryoet_data_portal import Annotation, Client
from dateutil.relativedelta import relativedelta as rd

from cryoet_data_portal_dashboard.util import month_range, table_bar, table_plot


@pn.cache(policy="LRU")
def get_annotations() -> list[Annotation]:
    """Get annotations."""
    # Get client instance
    client = Client()
    annotations = Annotation.find(client)
    return annotations


@pn.cache(policy="LRU")
def get_annotations_by_date(
    start: dt.date = dt(2020, 1, 1, tzinfo=tz.utc),
    end: dt.date = dt.now().date(),
) -> list[Annotation]:
    """Get annotations by date."""
    # Get client instance
    client = Client()
    annotations = Annotation.find(
        client,
        [
            Annotation.release_date >= dt.strftime(start, "%Y-%m-%d"),
            Annotation.release_date < dt.strftime(end, "%Y-%m-%d"),
        ],
    )
    return annotations


def annotations_per_month():
    """Get number of annotations per month."""
    daterange = month_range()

    dates = []
    nums = []

    for date in daterange:
        dates.append(date + rd(days=15))
        nums.append(len(get_annotations_by_date(start=date.date(), end=date.date() + rd(months=1))))

    return table_plot(
        dates,
        nums,
        "Annotations per Month",
        "Date",
        "Number of new Annotations",
    )


def cumulative_annotations_per_month():
    """Get cumulative number of annotations per month."""
    daterange = month_range()

    dates = []
    nums = []

    for date in daterange:
        dates.append(date)
        nums.append(len(get_annotations_by_date(end=date.date())))

    return table_plot(
        dates,
        nums,
        "Cumulative Annotations per Month",
        "Date",
        "Cumulative Number of Annotations",
    )


def annotations_by_method_type():
    """Get number of annotations by method type."""
    annotations = get_annotations()

    method_types = {a.method_type for a in annotations}
    method_type_counts = {}
    for method_type in method_types:
        method_type_counts[method_type] = len([a for a in annotations if a.method_type == method_type])

    return table_bar(
        list(method_type_counts.keys()),
        list(method_type_counts.values()),
        "Annotations by Method Type",
        "Method Type",
        "Number of Annotations",
    )
