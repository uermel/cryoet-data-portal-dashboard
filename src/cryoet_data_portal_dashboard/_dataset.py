from datetime import datetime as dt
from datetime import timezone as tz

import panel as pn
from cryoet_data_portal import Client, Dataset
from dateutil.relativedelta import relativedelta as rd

from cryoet_data_portal_dashboard.util import month_range, table_bar, table_plot


@pn.cache(policy="LRU")
def get_datasets() -> list[Dataset]:
    """Get datasets."""
    # Get client instance
    client = Client()
    datasets = Dataset.find(client)
    return datasets


@pn.cache(policy="LRU")
def get_datasets_by_date(
    start: dt.date = dt(2020, 1, 1, tzinfo=tz.utc),
    end: dt.date = dt.now().date(),
) -> list[Dataset]:
    """Get number of runs by date."""
    # Get client instance
    client = Client()
    runs = Dataset.find(
        client,
        [
            Dataset.release_date >= dt.strftime(start, "%Y-%m-%d"),
            Dataset.release_date < dt.strftime(end, "%Y-%m-%d"),
        ],
    )
    return runs


def datasets_per_month():
    """Get number of datasets per month."""
    # Get client instance
    daterange = month_range()

    dates = []
    nums = []

    for date in daterange:
        dates.append(date + rd(days=15))
        nums.append(len(get_datasets_by_date(start=date.date(), end=date.date() + rd(months=1))))

    return table_plot(
        dates,
        nums,
        "Datasets per Month",
        "Date",
        "Number of new Datasets",
    )


def cumulative_datasets_per_month():
    """Get cumulative number of datasets per month."""
    # Get client instance
    datasets = get_datasets()
    daterange = month_range()

    dates = []
    nums = []

    for date in daterange:
        dates.append(date)
        nums.append(len([d for d in datasets if d.release_date < date.date()]))

    return table_plot(
        dates,
        nums,
        "Cumulative Datasets per Month",
        "Date",
        "Cumulative Number of Datasets",
    )


def datasets_per_sample_type():
    """Get number of datasets per sample type."""
    # Get client instance
    datasets = get_datasets()
    types = ["cell", "tissue", "organism", "organelle", "virus", "in_vitro", "in_silico", "other"]
    types = sorted(types)

    nums = [len([d for d in datasets if d.sample_type == t]) for t in types]

    return table_bar(
        types,
        nums,
        "Datasets per Type",
        "Type",
        "Number of Datasets",
    )
