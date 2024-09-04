from datetime import datetime as dt
from datetime import timezone as tz

import panel as pn
from cryoet_data_portal import Client, Run
from dateutil.relativedelta import relativedelta as rd

from ._annotation import get_annotations_by_date
from cryoet_data_portal_dashboard._dataset import get_datasets
from cryoet_data_portal_dashboard.util import month_range, table_bar, table_plot


@pn.cache(policy="LRU")
def runs_by_date(
    start: dt.date = dt(2020, 1, 1, tzinfo=tz.utc),
    end: dt.date = dt.now().date(),
) -> list[Run]:
    """Get number of runs by date."""
    # Get client instance
    client = Client()
    runs = Run.find(
        client,
        [
            Run.dataset.release_date >= dt.strftime(start, "%Y-%m-%d"),
            Run.dataset.release_date <= dt.strftime(end, "%Y-%m-%d"),
        ],
    )
    return runs


@pn.cache(policy="LRU")
def runs_by_species(
    species: str,
) -> list[Run]:
    """Get number of runs by species."""
    # Get client instance
    client = Client()
    runs = Run.find(
        client,
        [
            Run.dataset.organism_name == species,
        ],
    )
    return runs


def runs_per_month():
    """Get number of runs per month."""
    daterange = month_range()

    dates = []
    nums = []

    for date in daterange:
        dates.append(date + rd(days=15))
        nums.append(len(runs_by_date(start=date.date(), end=date.date() + rd(months=1))))

    return table_plot(
        dates,
        nums,
        "Runs per Month",
        "Date",
        "Number of Runs",
    )


def cumulative_runs_per_month():
    """Get cumulative number of runs per month."""
    daterange = month_range()

    dates = []
    nums = []

    for date in daterange:
        dates.append(date)
        nums.append(len(runs_by_date(end=date.date())))

    return table_plot(
        dates,
        nums,
        "Cumulative Runs per Month",
        "Date",
        "Cumulative Number of Runs",
    )


def runs_per_species():
    """Get number of runs per species."""
    # Get all available runs
    datasets = get_datasets()

    # Get unique organism names
    species = [d.organism_name for d in datasets if d.organism_name is not None]
    unique_species = set(species)

    # Count the Runs
    num_runs_per_species = {}
    ds_per_species = {}
    for spec in unique_species:
        num_runs_per_species[spec] = len(list(runs_by_species(spec)))
        ds_per_species[spec] = [d.id for d in datasets if d.organism_name == spec]

    # Sort by number
    sorted_by_run = {t[0]: t[1] for t in sorted(num_runs_per_species.items(), key=lambda kv: (kv[1], kv[0]))}

    return table_bar(
        list(sorted_by_run.keys()),
        list(sorted_by_run.values()),
        "Runs per Species",
        "Species",
        "Number of Runs",
        xrotation=45,
    )


# def annotated_runs_per_month_chart():
#     """Get number of annotated runs per month."""
#     # Get client instance
#     client = Client()
#     daterange = list(rrule(MONTHLY, dtstart=dt(2023, 11, 1), until=dt.today()))
#
#     dates = []
#     nums = []
#
#     for date in daterange:
#         dbdate = dt.strftime(date, "%Y-%m-%d")
#         annos = Annotation.find(client, [Annotation.release_date < dbdate])
#         rname = [a.s3_metadata_path.split("/")[4] for a in annos]
#         rname = list(set(rname))
#         nums.append(len(rname))
#         dates.append(date)
