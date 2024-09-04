from datetime import datetime as dt
from datetime import timezone as tz

import panel as pn
from cryoet_data_portal import Client, Tomogram
from dateutil.relativedelta import relativedelta as rd
from cryoet_data_portal_dashboard.util import month_range, table_bar, table_plot


@pn.cache(policy="LRU")
def get_tomograms() -> list[Tomogram]:
    """Get tomograms."""
    # Get client instance
    client = Client()
    tomograms = Tomogram.find(client)
    return tomograms


@pn.cache(policy="LRU")
def get_tomograms_by_date(
    start: dt.date = dt(2020, 1, 1, tzinfo=tz.utc),
    end: dt.date = dt.now().date(),
) -> list[Tomogram]:
    """Get tomograms by date."""
    # Get client instance
    client = Client()
    tomograms = Tomogram.find(
        client,
        [
            Tomogram.tomogram_voxel_spacing.run.dataset.release_date >= dt.strftime(start, "%Y-%m-%d"),
            Tomogram.tomogram_voxel_spacing.run.dataset.release_date < dt.strftime(end, "%Y-%m-%d"),
        ],
    )
    return tomograms


def tomograms_per_month():
    """Get cumulative number of tomograms per month."""
    daterange = month_range()

    dates = []
    nums = []

    for date in daterange:
        dates.append(date)
        nums.append(len(get_tomograms_by_date(start=date.date(), end=date.date() + rd(months=1))))

    return table_plot(
        dates,
        nums,
        "Tomograms per Month",
        "Date",
        "Number of new Tomograms",
    )


def cumulative_tomograms_per_month():
    """Get cumulative number of tomograms per month."""
    daterange = month_range()

    dates = []
    nums = []

    for date in daterange:
        dates.append(date)
        nums.append(len(get_tomograms_by_date(end=date.date())))

    return table_plot(
        dates,
        nums,
        "Cumulative Tomograms per Month",
        "Date",
        "Cumulative Number of Tomograms",
    )


def tomograms_by_reconstruction_method():
    """Get number of tomograms by reconstruction method."""
    tomograms = get_tomograms()

    recon_methods = {t.reconstruction_method for t in tomograms}

    methods = []
    nums = []

    for method in recon_methods:
        methods.append(method)
        nums.append(len([t for t in tomograms if t.reconstruction_method == method]))

    return table_bar(
        methods,
        nums,
        "Tomograms by Reconstruction Method",
        "Reconstruction Method",
        "Number of Tomograms",
    )
