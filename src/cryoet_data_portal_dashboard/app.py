import holoviews as hv
import panel as pn
import pandas as pd

# from cryoet_data_portal_dashboard._annotation import (
#     annotations_by_method_type,
#     annotations_per_month,
#     cumulative_annotations_per_month,
# )
# from cryoet_data_portal_dashboard._dataset import (
#     cumulative_datasets_per_month,
#     datasets_per_month,
#     datasets_per_sample_type,
# )
# from cryoet_data_portal_dashboard._run import cumulative_runs_per_month, runs_per_month, runs_per_species
# from cryoet_data_portal_dashboard._tomogram import (
#     cumulative_tomograms_per_month,
#     tomograms_by_reconstruction_method,
#     tomograms_per_month,
# )

pn.extension(nthreads=8, sizing_mode="stretch_width", template="material", defer_load=True)
hv.extension("bokeh")


### Util
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


### Util
@pn.cache(policy="LRU")
def load_datasets_per_month():
    """Load datasets per month."""
    return pd.read_csv("data/datasets_per_month.csv")


def datasets_per_month():
    """Get number of datasets per month."""
    df = load_datasets_per_month()
    print(df)
    print(df.columns)
    return table_plot(
        df["date"],
        df["num"],
        "Datasets per Month",
        "Date",
        "Number of new Datasets",
    )


datasets = pn.Column(
    datasets_per_month(),
    # cumulative_datasets_per_month(),
    # datasets_per_sample_type(),
)

# runs = pn.Column(
#     runs_per_species(),
#     runs_per_month(),
#     cumulative_runs_per_month(),
# )
#
# tomograms = pn.Column(
#     tomograms_per_month(),
#     cumulative_tomograms_per_month(),
#     tomograms_by_reconstruction_method(),
# )
#
# annotations = pn.Column(
#     annotations_per_month(),
#     cumulative_annotations_per_month(),
#     annotations_by_method_type(),
# )

app = pn.Tabs(
    ("Datasets", datasets),
    # ("Runs", runs),
    # ("Tomograms", tomograms),
    # ("Annotations", annotations),
)
app.servable(title="cryoET Data Portal dashboard", area="main")
