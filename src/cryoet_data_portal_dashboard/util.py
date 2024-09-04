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


def plot(x, y, title, xlabel, ylabel, color="g", width=800, height=400):
    """Plot a curve."""
    crv = hv.Curve((x, y), kdims=xlabel, vdims=ylabel).opts(
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        color=color,
        width=width,
        height=height,
        show_grid=True,
    )

    sct = hv.Scatter((x, y), kdims=xlabel, vdims=ylabel).opts(
        color=color,
        size=5,
        tools=["hover"],
    )

    return crv * sct


def table(x, y, title, xlabel, ylabel):
    """Plot a table."""
    tbl = hv.Table((x, y), kdims=xlabel, vdims=ylabel).opts(
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
    )

    return tbl


def bar(x, y, title, xlabel, ylabel, color="g", width=800, height=400, xrotation=0):
    """Plot a bar."""
    b = hv.Bars((x, y), kdims=xlabel, vdims=ylabel).opts(
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        color=color,
        width=width,
        height=height,
        show_grid=True,
        xrotation=xrotation,
    )

    return b


def table_plot(x, y, title, xlabel, ylabel, color="g", width=800, height=400):
    """Plot a table and a curve."""
    tbl = table(x, y, title, xlabel, ylabel)
    crv = plot(x, y, title, xlabel, ylabel, color, width, height)

    return pn.Row(tbl, crv)


def table_bar(x, y, title, xlabel, ylabel, color="g", width=800, height=400, xrotation=0):
    """Plot a table and a bar."""
    tbl = table(x, y, title, xlabel, ylabel)
    b = bar(x, y, title, xlabel, ylabel, color, width, height, xrotation)

    return pn.Row(tbl, b)
