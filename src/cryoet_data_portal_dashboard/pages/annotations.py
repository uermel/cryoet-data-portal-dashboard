"""Annotations page for the dashboard."""
import pandas as pd
from dash import dcc, html, callback, Output, Input, dash_table, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
from datetime import datetime
from dash.dependencies import Input, Output, State, ALL
import os

from cryoet_data_portal_dashboard.components import (
    create_card, 
    create_date_range_selector, 
    filter_by_date_range,
    group_by_interval,
    calculate_cumulative,
    create_line_chart,
    create_bar_chart,
    generate_csv_download,
    generate_svg_download
)
from cryoet_data_portal_dashboard.data_utils import (
    fetch_annotations,
    get_annotations_by_method,
    get_annotations_by_shape,
    get_annotations_by_object,
    get_example_annotation_shapes
)
from cryoet_data_portal_dashboard.cache import cache

# Define the layout for the annotations page
layout = dbc.Container(
    [
        dcc.Location(id="annotations-url", refresh=False),  # Add location component to provide input for callbacks
        html.H2("Annotations", className="mb-3"),  # Changed from H1 to H2 and removed "Dashboard"
        
        # Card 1: Number of annotations added per month
        create_card(
            title="Number of Annotations Added Per Month",
            table_component=html.Div(
                [
                    create_date_range_selector("annotations-added"),
                    html.Div(id="annotations-added-table"),
                ]
            ),
            plot_component=dcc.Graph(id="annotations-added-plot"),
            id_prefix="annotations-added"
        ),
        
        # Card 2: Cumulative number of annotations per month
        create_card(
            title="Cumulative Number of Annotations",
            table_component=html.Div(
                [
                    create_date_range_selector("annotations-cumulative"),
                    html.Div(id="annotations-cumulative-table"),
                ]
            ),
            plot_component=dcc.Graph(id="annotations-cumulative-plot"),
            id_prefix="annotations-cumulative"
        ),
        
        # Card 3: Annotations per method type
        create_card(
            title="Annotations by Method Type",
            table_component=html.Div(id="annotations-method-table"),
            plot_component=dcc.Graph(id="annotations-method-plot"),
            id_prefix="annotations-method"
        ),
        
        # Card 4: Annotations by Shape Type
        create_card(
            title="Annotation Shapes by Type",
            table_component=html.Div(id="annotations-shape-table"),
            plot_component=dcc.Graph(id="annotations-shape-plot"),
            id_prefix="annotations-shape"
        ),
        
        # Shape Type Explanations Section
        html.Div(id="shape-type-explanations", className="mt-3 mb-4"),
        
        # Card 5: Annotations by Object Name
        create_card(
            title="Annotations by Annotated Object Name",
            table_component=html.Div(id="annotations-object-table"),
            plot_component=dcc.Graph(id="annotations-object-plot"),
            id_prefix="annotations-object"
        ),
    ],
    fluid=True,
    className="py-3",
)


# Callback for annotations added per month
@callback(
    [Output("annotations-added-table", "children"),
     Output("annotations-added-plot", "figure")],
    [Input("annotations-added-date-range", "start_date"),
     Input("annotations-added-date-range", "end_date"),
     Input("annotations-added-interval", "value"),
     Input("annotations-added-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_annotations_added(start_date, end_date, interval, n_clicks):
    # Fetch data
    df = fetch_annotations()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Create the table
    table = dash_table.DataTable(
        data=grouped_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Annotations Added", "id": "count"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
    )
    
    # Create the plot
    fig = create_line_chart(
        grouped_df, 
        date_col, 
        'count', 
        "Annotations Added Over Time",
        labels={"count": "Number of Annotations", date_col: "Date"}
    )
    
    return table, fig


# Callback for cumulative annotations
@callback(
    [Output("annotations-cumulative-table", "children"),
     Output("annotations-cumulative-plot", "figure")],
    [Input("annotations-cumulative-date-range", "start_date"),
     Input("annotations-cumulative-date-range", "end_date"),
     Input("annotations-cumulative-interval", "value"),
     Input("annotations-cumulative-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_annotations_cumulative(start_date, end_date, interval, n_clicks):
    # Fetch data
    df = fetch_annotations()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Calculate cumulative
    cumulative_df = calculate_cumulative(grouped_df, date_col)
    
    # Create the table
    table = dash_table.DataTable(
        data=cumulative_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Annotations Added", "id": "count"},
            {"name": "Cumulative Annotations", "id": "cumulative"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
    )
    
    # Create the plot
    fig = create_line_chart(
        cumulative_df, 
        date_col, 
        'cumulative', 
        "Cumulative Annotations Over Time",
        labels={"cumulative": "Total Number of Annotations", date_col: "Date"}
    )
    
    return table, fig


# Callback for annotations by method
@callback(
    [Output("annotations-method-table", "children"),
     Output("annotations-method-plot", "figure")],
    [Input("annotations-url", "pathname"),
     Input("annotations-method-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_annotations_by_method(pathname, n_clicks):
    # Get data
    df = get_annotations_by_method()
    
    # Create the table
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {"name": "Method Type", "id": "method_type"},
            {"name": "Count", "id": "count"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
    )
    
    # Create the plot
    fig = create_bar_chart(
        df, 
        'method_type', 
        'count', 
        "Annotations by Method Type",
        labels={"count": "Number of Annotations", "method_type": "Method Type"}
    )
    
    return table, fig


# Callback for annotations by shape
@callback(
    [Output("annotations-shape-table", "children"),
     Output("annotations-shape-plot", "figure")],
    [Input("annotations-url", "pathname"),
     Input("annotations-shape-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_annotations_by_shape(pathname, n_clicks):
    # Get data
    df = get_annotations_by_shape()
    
    # Create the table
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {"name": "Shape Type", "id": "shape_type"},
            {"name": "Count", "id": "count"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
    )
    
    # Create the plot
    fig = create_bar_chart(
        df, 
        'shape_type', 
        'count', 
        "Annotations by Shape Type",
        labels={"count": "Number of Annotation Shapes", "shape_type": "Shape Type"}
    )
    
    return table, fig


# Add a new callback to show shape type explanations
@callback(
    Output("shape-type-explanations", "children"),
    [Input("annotations-url", "pathname")]
)
def display_shape_type_explanations(pathname):
    """Display explanations for the different annotation shape types."""
    # Get the examples to potentially show alongside explanations
    examples_df = get_example_annotation_shapes()
    
    # Create descriptions for each shape type
    shape_type_descriptions = {
        "SegmentationMask": "A 3D volume where each voxel is labeled to indicate whether it belongs to the annotated object. Used for outlining complete structures.",
        "InstanceSegmentation": "Similar to segmentation masks, but each instance of an object gets a unique ID, allowing multiple objects of the same type to be distinguished.",
        "Point": "Simple point annotations marking locations of interest in 3D space. Typically used to mark the center or a specific feature of an object.",
        "OrientedPoint": "Point annotations that also include orientation information, showing direction or alignment of the annotated feature.",
        "Mesh": "A 3D surface representation consisting of vertices, edges, and faces. Provides a detailed surface model of the annotated structure."
    }
    
    # Create cards for each shape type
    shape_type_cards = []
    for shape_type, description in shape_type_descriptions.items():
        # Format the shape type for display
        display_name = shape_type.capitalize().replace('_', ' ')
        
        # Check if we have examples for this shape type
        examples = examples_df[examples_df['shape_type'] == shape_type].to_dict('records') if not examples_df.empty else []
        example_count = len(examples)
        
        # Create the card
        card = dbc.Card(
            dbc.CardBody([
                html.H5(display_name, className="card-title"),
                html.P(description, className="card-text"),
                html.P(f"There are {example_count} example(s) of this shape type in the database." if example_count > 0 else "No examples of this shape type in the database.", 
                       className="card-text text-muted"),
            ]),
            className="mb-3"
        )
        shape_type_cards.append(card)
    
    return html.Div([
        html.H4("Annotation Shape Types Explained", className="mt-4 mb-3"),
        html.P("Annotation shapes are the geometric representations used to mark structures in tomograms. Each shape type serves a different purpose:"),
        html.Div(shape_type_cards)
    ])


# Callback for annotations by object
@callback(
    [Output("annotations-object-table", "children"),
     Output("annotations-object-plot", "figure")],
    [Input("annotations-url", "pathname"),
     Input("annotations-object-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_annotations_by_object(pathname, n_clicks):
    # Get data
    df = get_annotations_by_object()
    
    # Create the table
    if df.empty:
        table = html.Div("No data available")
    else:
        # Convert the DataFrame to a list of rows for display
        rows = []
        for i, row in df.iterrows():
            # Create a clickable link if URL exists
            if row['url']:
                object_name_cell = html.Td([
                    html.A(
                        row['object_name'],
                        href=row['url'],
                        target="_blank",  # Open in new tab
                        style={'color': '#007bff', 'textDecoration': 'underline'}
                    )
                ])
            else:
                object_name_cell = html.Td(row['object_name'])
                
            rows.append(html.Tr([
                object_name_cell,
                html.Td(row['count'])
            ]))
        
        # Create a table using html components instead of DataTable
        table = html.Table(
            [
                html.Thead(
                    html.Tr([
                        html.Th("Object Name", style={'fontWeight': 'bold', 'textAlign': 'left'}),
                        html.Th("Count", style={'fontWeight': 'bold', 'textAlign': 'left'})
                    ])
                ),
                html.Tbody(rows)
            ],
            style={'width': '100%', 'overflowX': 'auto'}
        )
    
    # Create the plot
    fig = create_bar_chart(
        df, 
        'object_name', 
        'count', 
        "Annotations by Annotated Object Name",
        labels={"count": "Number of Annotations", "object_name": "Object Name"}
    )
    
    return table, fig


# Callbacks for SVG downloads
@callback(
    Output(f"annotations-added-download-svg", "data"),
    Input("annotations-added-download-svg-button", "n_clicks"),
    State("annotations-added-plot", "figure"),
    prevent_initial_call=True,
)
def download_annotations_added_svg(n_clicks, figure):
    """Download the annotations added chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "annotations_added")


@callback(
    Output(f"annotations-cumulative-download-svg", "data"),
    Input("annotations-cumulative-download-svg-button", "n_clicks"),
    State("annotations-cumulative-plot", "figure"),
    prevent_initial_call=True,
)
def download_annotations_cumulative_svg(n_clicks, figure):
    """Download the cumulative annotations chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "annotations_cumulative")


@callback(
    Output(f"annotations-method-download-svg", "data"),
    Input("annotations-method-download-svg-button", "n_clicks"),
    State("annotations-method-plot", "figure"),
    prevent_initial_call=True,
)
def download_annotations_method_svg(n_clicks, figure):
    """Download the annotations by method chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "annotations_by_method")


@callback(
    Output(f"annotations-shape-download-svg", "data"),
    Input("annotations-shape-download-svg-button", "n_clicks"),
    State("annotations-shape-plot", "figure"),
    prevent_initial_call=True,
)
def download_annotations_shape_svg(n_clicks, figure):
    """Download the annotations by shape chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "annotations_by_shape")


@callback(
    Output(f"annotations-object-download-svg", "data"),
    Input("annotations-object-download-svg-button", "n_clicks"),
    State("annotations-object-plot", "figure"),
    prevent_initial_call=True,
)
def download_annotations_object_svg(n_clicks, figure):
    """Download the annotations by object chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "annotations_by_object") 