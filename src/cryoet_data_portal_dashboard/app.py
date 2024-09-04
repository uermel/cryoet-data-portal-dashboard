import holoviews as hv
import panel as pn

from cryoet_data_portal_dashboard._annotation import (
    annotations_by_method_type,
    annotations_per_month,
    cumulative_annotations_per_month,
)
from cryoet_data_portal_dashboard._dataset import (
    cumulative_datasets_per_month,
    datasets_per_month,
    datasets_per_sample_type,
)
from cryoet_data_portal_dashboard._run import cumulative_runs_per_month, runs_per_month, runs_per_species
from cryoet_data_portal_dashboard._tomogram import (
    cumulative_tomograms_per_month,
    tomograms_by_reconstruction_method,
    tomograms_per_month,
)

pn.extension(nthreads=8, sizing_mode="stretch_width", template="material", defer_load=True)
hv.extension("bokeh")

datasets = pn.Column(
    datasets_per_month(),
    cumulative_datasets_per_month(),
    datasets_per_sample_type(),
)

runs = pn.Column(
    runs_per_species(),
    runs_per_month(),
    cumulative_runs_per_month(),
)

tomograms = pn.Column(
    tomograms_per_month(),
    cumulative_tomograms_per_month(),
    tomograms_by_reconstruction_method(),
)

annotations = pn.Column(
    annotations_per_month(),
    cumulative_annotations_per_month(),
    annotations_by_method_type(),
)

app = pn.Tabs(
    ("Datasets", datasets),
    ("Runs", runs),
    ("Tomograms", tomograms),
    ("Annotations", annotations),
)
app.servable(title="cryoET Data Portal dashboard", area="main")
