"""Main application for the cryoET Data Portal Dashboard."""
# Configure logging first, before any other imports
import logging

# Suppress logs from GraphQL and related libraries globally
logging.getLogger('gql').setLevel(logging.WARNING)
logging.getLogger('gql.transport').setLevel(logging.WARNING)
logging.getLogger('gql.transport.requests').setLevel(logging.WARNING)
logging.getLogger('gql.dsl').setLevel(logging.WARNING)
logging.getLogger('cryoet_data_portal').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import os

from cryoet_data_portal_dashboard import cache as cache_module

# Initialize the app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://use.fontawesome.com/releases/v5.15.4/css/all.css'  # For the refresh icon
    ],
    suppress_callback_exceptions=True,
)

server = app.server

# Initialize the cache
cache = cache_module.init_cache(server)

# Import pages after initializing the app and cache to avoid circular imports
from cryoet_data_portal_dashboard.pages import (
    depositions,
    datasets,
    runs,
    tomograms,
    annotations,
)

# Import and start the data preloader
from cryoet_data_portal_dashboard.preloader import preload_data_in_background
preload_thread = preload_data_in_background()

# Get a logger for this module
logger = logging.getLogger(__name__)
logger.info("Starting cryoET Data Portal Dashboard with background data preloading")

# Create the basic layout with a sidebar and content area
app.layout = dbc.Container(
    [
        # Header row with title
        dbc.Row(
            dbc.Col(
                html.H1("CryoET Data Portal Dashboard", className="text-center my-4"),
                width=12
            ),
            className="mb-2"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Hr(),
                        html.P(
                            "Navigation", className="lead"
                        ),
                        dbc.Nav(
                            [
                                dbc.NavLink("Depositions", href="/depositions", active="exact"),
                                dbc.NavLink("Datasets", href="/datasets", active="exact"),
                                dbc.NavLink("Runs", href="/runs", active="exact"),
                                dbc.NavLink("Tomograms", href="/tomograms", active="exact"),
                                dbc.NavLink("Annotations", href="/annotations", active="exact"),
                            ],
                            vertical=True,
                            pills=True,
                        ),
                        html.Hr(),
                        html.Div(
                            [
                                html.P(
                                    "CryoET Data Portal Dashboard shows visualizations and statistics of the cryoET data portal.",
                                    className="small text-muted"
                                ),
                                html.P(
                                    html.A(
                                        "Visit CryoET Data Portal",
                                        href="https://cryoetdataportal.czscience.com/",
                                        target="_blank"
                                    ),
                                    className="small"
                                )
                            ],
                            className="mt-4"
                        )
                    ],
                    width=2,
                    className="bg-light p-4"
                ),
                dbc.Col(
                    [
                        dcc.Location(id="url", refresh=False),
                        html.Div(id="page-content")
                    ],
                    width=10
                ),
            ]
        ),
    ],
    fluid=True,
)


# Define callback to render the appropriate page content
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/depositions" or pathname == "/":
        return depositions.layout
    elif pathname == "/datasets":
        return datasets.layout
    elif pathname == "/runs":
        return runs.layout
    elif pathname == "/tomograms":
        return tomograms.layout
    elif pathname == "/annotations":
        return annotations.layout
    else:
        # If the user tries to navigate to a non-existent page
        return dbc.Container(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognized..."),
            ]
        )


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
