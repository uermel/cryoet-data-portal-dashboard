"""Tomograms page for the dashboard."""
import pandas as pd
from dash import dcc, html, callback, Output, Input, dash_table, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
from datetime import datetime
import logging
import random
import dash
from dash import State
import plotly.graph_objects as go
import os

from cryoet_data_portal_dashboard.components import (
    create_card, 
    create_date_range_selector, 
    filter_by_date_range,
    group_by_interval,
    calculate_cumulative,
    create_line_chart,
    create_bar_chart,
    create_auto_scrolling_image_gallery,
    create_related_items_grid_gallery,
    generate_csv_download,
    generate_svg_download
)
from cryoet_data_portal_dashboard.data_utils import (
    fetch_tomograms,
    get_tomograms_by_reconstruction_method,
    get_tomograms_by_processing_method,
    get_tomograms_by_voxel_spacing,
    get_tomogram_images,
    PORTAL_BASE_URL
)
from cryoet_data_portal_dashboard.cache import cache

logger = logging.getLogger(__name__)

# Get tomogram images for the gallery
tomogram_images = get_tomogram_images()

# Define the layout for the tomograms page
layout = dbc.Container(
    [
        dcc.Location(id="tomograms-url", refresh=False),  # Add location component to provide input for callbacks
        html.H2("Tomograms", className="mb-3"),  # Changed from H1 to H2 and removed "Dashboard"
        
        # Image Gallery
        create_auto_scrolling_image_gallery(
            tomogram_images, 
            "Example Tomograms"
        ),
        
        # Interactive Table Info Alert
        dbc.Alert(
            [
                html.H5("Interactive Table Instructions", className="alert-heading"),
                html.P(
                    "The tables below are interactive. Click on any row to highlight it and view related tomogram "
                    "data. A gallery of related tomogram images will appear below the chart. You can filter data using "
                    "the date range selectors. For reconstruction method and processing method tables, clicking on a row "
                    "will show tomograms processed with that specific method."
                ),
            ],
            color="info",
            className="mb-4",
        ),
        
        # Card 1: Number of tomograms added per month
        create_card(
            title="Number of Tomograms Added Per Month",
            table_component=html.Div(
                [
                    create_date_range_selector("tomograms-added"),
                    html.Div(id="tomograms-added-table"),
                ]
            ),
            plot_component=dcc.Graph(id="tomograms-added-plot"),
            id_prefix="tomograms-added"
        ),
        
        # Card 2: Cumulative number of tomograms per month
        create_card(
            title="Cumulative Number of Tomograms",
            table_component=html.Div(
                [
                    create_date_range_selector("tomograms-cumulative"),
                    html.Div(id="tomograms-cumulative-table"),
                ]
            ),
            plot_component=dcc.Graph(id="tomograms-cumulative-plot"),
            id_prefix="tomograms-cumulative"
        ),
        
        # Card 3: Tomograms per reconstruction method
        create_card(
            title="Tomograms by Reconstruction Method",
            table_component=html.Div(id="tomograms-recon-method-table"),
            plot_component=dcc.Graph(id="tomograms-recon-method-plot"),
            id_prefix="tomograms-recon-method"
        ),
        
        # Card 4: Tomograms per processing method
        create_card(
            title="Tomograms by Processing Method",
            table_component=html.Div(id="tomograms-proc-method-table"),
            plot_component=dcc.Graph(id="tomograms-proc-method-plot"),
            id_prefix="tomograms-proc-method"
        ),
        
        # Card 5: Tomograms vs voxel spacing
        create_card(
            title="Tomograms by Voxel Spacing",
            table_component=html.Div(id="tomograms-voxel-spacing-table"),
            plot_component=dcc.Graph(id="tomograms-voxel-spacing-plot"),
            id_prefix="tomograms-voxel-spacing"
        ),
    ],
    fluid=True,
    className="py-3",
)


# Callback for tomograms added per month
@callback(
    [Output("tomograms-added-table", "children"),
     Output("tomograms-added-plot", "figure")],
    [Input("tomograms-added-date-range", "start_date"),
     Input("tomograms-added-date-range", "end_date"),
     Input("tomograms-added-interval", "value"),
     Input("tomograms-added-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_tomograms_added(start_date, end_date, interval, n_clicks):
    # Fetch data
    df = fetch_tomograms()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Create the table
    table = dash_table.DataTable(
        id='tomograms-added-datatable',
        data=grouped_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Tomograms Added", "id": "count"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
        # Add CSS classes for interactive behavior
        row_selectable=False,
        cell_selectable=True,
        style_data_conditional=[
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                'border': '1px solid rgb(0, 116, 217)'
            }
        ],
    )
    
    # Create the plot
    fig = create_line_chart(
        grouped_df, 
        date_col, 
        'count', 
        "Tomograms Added Over Time",
        labels={"count": "Number of Tomograms", date_col: "Date"}
    )
    
    return table, fig


# Callback for cumulative tomograms
@callback(
    [Output("tomograms-cumulative-table", "children"),
     Output("tomograms-cumulative-plot", "figure")],
    [Input("tomograms-cumulative-date-range", "start_date"),
     Input("tomograms-cumulative-date-range", "end_date"),
     Input("tomograms-cumulative-interval", "value"),
     Input("tomograms-cumulative-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_tomograms_cumulative(start_date, end_date, interval, n_clicks):
    # Fetch data
    df = fetch_tomograms()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Calculate cumulative sum
    cumulative_df = calculate_cumulative(grouped_df, date_col)
    
    # Create the table
    table = dash_table.DataTable(
        id='tomograms-cumulative-datatable',
        data=cumulative_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Cumulative Tomograms", "id": "cumulative"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
        # Add CSS classes for interactive behavior
        row_selectable=False,
        cell_selectable=True,
        style_data_conditional=[
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                'border': '1px solid rgb(0, 116, 217)'
            }
        ],
    )
    
    # Create the plot
    fig = create_line_chart(
        cumulative_df, 
        date_col, 
        'cumulative', 
        "Cumulative Tomograms Over Time",
        labels={"cumulative": "Total Number of Tomograms", date_col: "Date"}
    )
    
    return table, fig


# Callback for tomograms by reconstruction method
@callback(
    [Output("tomograms-recon-method-table", "children"),
     Output("tomograms-recon-method-plot", "figure")],
    [Input("tomograms-url", "pathname"),
     Input("tomograms-recon-method-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_tomograms_by_recon_method(pathname, n_clicks):
    # Get data
    df = get_tomograms_by_reconstruction_method()
    
    # Create the table
    table = dash_table.DataTable(
        id='tomograms-recon-method-datatable',
        data=df.to_dict('records'),
        columns=[
            {"name": "Reconstruction Method", "id": "reconstruction_method"},
            {"name": "Count", "id": "count"},
            {"name": "Percentage", "id": "percentage", "type": "numeric", "format": {"specifier": ".2%"}}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
        # Add CSS classes for interactive behavior
        row_selectable=False,
        cell_selectable=True,
        style_data_conditional=[
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                'border': '1px solid rgb(0, 116, 217)'
            }
        ],
    )
    
    # Create the plot
    fig = create_bar_chart(
        df, 
        'reconstruction_method', 
        'count', 
        "Tomograms by Reconstruction Method",
        labels={"count": "Number of Tomograms", "reconstruction_method": "Reconstruction Method"}
    )
    
    return table, fig


# Callback for tomograms by processing method
@callback(
    [Output("tomograms-proc-method-table", "children"),
     Output("tomograms-proc-method-plot", "figure")],
    [Input("tomograms-url", "pathname"),
     Input("tomograms-proc-method-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_tomograms_by_proc_method(pathname, n_clicks):
    # Get data
    df = get_tomograms_by_processing_method()
    
    # Create the table
    table = dash_table.DataTable(
        id='tomograms-proc-method-datatable',
        data=df.to_dict('records'),
        columns=[
            {"name": "Processing Method", "id": "processing_method"},
            {"name": "Count", "id": "count"},
            {"name": "Percentage", "id": "percentage", "type": "numeric", "format": {"specifier": ".2%"}}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
        # Add CSS classes for interactive behavior
        row_selectable=False,
        cell_selectable=True,
        style_data_conditional=[
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                'border': '1px solid rgb(0, 116, 217)'
            }
        ],
    )
    
    # Create the plot
    fig = create_bar_chart(
        df, 
        'processing_method', 
        'count', 
        "Tomograms by Processing Method",
        labels={"count": "Number of Tomograms", "processing_method": "Processing Method"}
    )
    
    return table, fig


# Callback for tomograms by voxel spacing
@callback(
    [Output("tomograms-voxel-spacing-table", "children"),
     Output("tomograms-voxel-spacing-plot", "figure")],
    [Input("tomograms-url", "pathname"),
     Input("tomograms-voxel-spacing-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_tomograms_by_voxel_spacing(pathname, n_clicks):
    try:
        # Get data
        df = get_tomograms_by_voxel_spacing()
        
        logger.info(f"Voxel spacing data: columns={list(df.columns)}, count={len(df)}")
        
        # Ensure the column names are correct
        if 'voxel_spacing_rounded' in df.columns and 'voxel_spacing' not in df.columns:
            # Rename column for display
            df = df.rename(columns={'voxel_spacing_rounded': 'voxel_spacing'})
        
        # Create the table
        table = dash_table.DataTable(
            id='tomograms-voxel-spacing-datatable',
            data=df.to_dict('records'),
            columns=[
                {"name": "Voxel Spacing (Å)", "id": "voxel_spacing"},
                {"name": "Count", "id": "count"}
            ],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            style_header={'fontWeight': 'bold'},
            # Add CSS classes for interactive behavior
            row_selectable=False,
            cell_selectable=True,
            style_data_conditional=[
                {
                    'if': {'state': 'active'},
                    'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                    'border': '1px solid rgb(0, 116, 217)'
                }
            ],
        )
        
        # Create the plot
        fig = create_bar_chart(
            df, 
            'voxel_spacing', 
            'count', 
            "Tomograms by Voxel Spacing",
            labels={"count": "Number of Tomograms", "voxel_spacing": "Voxel Spacing (Å)"}
        )
        
        return table, fig
    
    except Exception as e:
        logger.exception(f"Error in update_tomograms_by_voxel_spacing: {str(e)}")
        # Return empty table and figure on error
        empty_df = pd.DataFrame(columns=['voxel_spacing', 'count'])
        empty_table = dash_table.DataTable(
            id='tomograms-voxel-spacing-datatable',
            data=[],
            columns=[
                {"name": "Voxel Spacing (Å)", "id": "voxel_spacing"},
                {"name": "Count", "id": "count"}
            ],
        )
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="No voxel spacing data available",
            xaxis_title="Voxel Spacing (Å)",
            yaxis_title="Number of Tomograms"
        )
        return empty_table, empty_fig


# Callback for refreshing the gallery
@callback(
    Output("example-tomograms-gallery", "children"),
    Input("example-tomograms-refresh-button", "n_clicks")
)
def refresh_tomogram_images(n_clicks):
    """
    Refresh the tomogram images gallery when the reshuffle button is clicked.
    """
    if n_clicks is None:
        return no_update
    
    # Get fresh random images, using n_clicks as a cache buster
    images = get_tomogram_images(cache_buster=n_clicks)
    logger.info(f"Got {len(images)} images from get_tomogram_images(), cache_buster={n_clicks}")
    
    # Limit to 50 images before duplication
    images = images[:50]
    logger.info(f"Limited to {len(images)} images before creating cards")
    
    # Create image cards with clickable links
    image_cards = []
    for img in images:
        if img.get('url'):
            # Ensure link is a full URL to the external data portal
            external_link = img.get('link', '#')
            
            # Create a card with a link
            image_cards.append(
                html.Div([
                    html.A([
                        html.Img(
                            src=img['url'],
                            style={
                                "height": "120px",
                                "objectFit": "cover",
                                "borderRadius": "4px",
                                "width": "100%"
                            }
                        ),
                        html.Div(
                            img.get('caption', ''),
                            style={
                                "fontSize": "12px",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "whiteSpace": "nowrap",
                                "maxWidth": "150px",
                                "textAlign": "center",
                                "marginTop": "5px"
                            }
                        )
                    ], 
                    href=external_link,
                    target="_blank",
                    title=f"View {img.get('caption', 'item')} details in the Data Portal",
                    style={"textDecoration": "none", "color": "inherit"},
                    className="external-link"
                    )
                ],
                className="image-card")
            )
    
    logger.info(f"Created {len(image_cards)} image cards")
    
    # Duplicate the cards to create a seamless scrolling effect
    all_cards = image_cards + image_cards
    logger.info(f"Total cards after duplication: {len(all_cards)}")
    
    return all_cards 

# Callback to show a grid gallery of related tomograms for the tomograms-added table
@callback(
    [Output("tomograms-added-related-items", "children"),
     Output("tomograms-added-related-items-collapse", "is_open")],
    [Input("tomograms-added-datatable", "active_cell"),
     Input("tomograms-added-datatable", "data")]
)
def display_tomograms_added_related_items(active_cell, data):
    """
    Display a grid gallery of tomograms added during the selected time period.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related tomograms"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        selected_date = selected_row['deposition_date']
        
        logger.info(f"Tomograms Added - Selected date: {selected_date}")
        
        # Fetch all tomograms
        all_tomograms = fetch_tomograms()
        
        # Convert the selected date string to a datetime object for comparison
        selected_date = pd.to_datetime(selected_date)
        
        # Extract year and month from selected date for filtering
        selected_year_month = selected_date.strftime('%Y-%m')
        
        # Filter tomograms with matching year-month
        all_tomograms['year_month'] = pd.to_datetime(all_tomograms['deposition_date']).dt.strftime('%Y-%m')
        related_tomograms = all_tomograms[all_tomograms['year_month'] == selected_year_month]
        
        logger.info(f"Tomograms Added - Found {len(related_tomograms)} related tomograms for {selected_year_month}")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_tomograms.to_dict('records')
        
        # Create the grid gallery component
        gallery = create_related_items_grid_gallery(related_items, 'tomogram', f"Tomograms added in {selected_year_month}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.exception(f"Error displaying related tomograms: {str(e)}")
        return html.P(f"Error displaying related tomograms: {str(e)}"), True

# Callback to show a grid gallery of related tomograms for the tomograms-cumulative table
@callback(
    [Output("tomograms-cumulative-related-items", "children"),
     Output("tomograms-cumulative-related-items-collapse", "is_open")],
    [Input("tomograms-cumulative-datatable", "active_cell"),
     Input("tomograms-cumulative-datatable", "data")]
)
def display_tomograms_cumulative_related_items(active_cell, data):
    """
    Display a grid gallery of tomograms up to the selected time period.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related tomograms"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        selected_date = selected_row['deposition_date']
        
        logger.info(f"Tomograms Cumulative - Selected date: {selected_date}")
        
        # Fetch all tomograms
        all_tomograms = fetch_tomograms()
        
        # Convert the selected date string to a date object (without time) for comparison
        selected_date = pd.to_datetime(selected_date).date()
        
        # Create a date_only column in the DataFrame to avoid timezone comparison issues
        all_tomograms['date_only'] = pd.to_datetime(all_tomograms['deposition_date']).dt.date
        
        # Filter tomograms up to and including that date using the date_only column
        related_tomograms = all_tomograms[all_tomograms['date_only'] <= selected_date]
        
        logger.info(f"Tomograms Cumulative - Found {len(related_tomograms)} related tomograms up to {selected_date}")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_tomograms.to_dict('records')
        
        # Create the grid gallery component
        gallery = create_related_items_grid_gallery(related_items, 'tomogram', f"Tomograms up to {selected_date}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.exception(f"Error displaying related tomograms: {str(e)}")
        return html.P(f"Error displaying related tomograms: {str(e)}"), True

# Callback to show a grid gallery of related tomograms for the reconstruction method table
@callback(
    [Output("tomograms-recon-method-related-items", "children"),
     Output("tomograms-recon-method-related-items-collapse", "is_open")],
    [Input("tomograms-recon-method-datatable", "active_cell"),
     Input("tomograms-recon-method-datatable", "data")]
)
def display_tomograms_recon_method_related_items(active_cell, data):
    """
    Display a grid gallery of tomograms for the selected reconstruction method.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related tomograms"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        recon_method = selected_row['reconstruction_method']
        
        logger.info(f"Tomograms Recon Method - Selected method: {recon_method}")
        
        # Fetch all tomograms
        all_tomograms = fetch_tomograms()
        
        # Filter tomograms for the selected reconstruction method
        related_tomograms = all_tomograms[all_tomograms['reconstruction_method'] == recon_method]
        
        logger.info(f"Tomograms Recon Method - Found {len(related_tomograms)} related tomograms for {recon_method}")
        logger.info(f"Tomograms columns: {list(related_tomograms.columns)}")
        
        # Check if key_photo_url exists and is not empty
        if 'key_photo_url' not in related_tomograms.columns:
            logger.error("key_photo_url column not found in tomograms data")
            return html.P(f"Error: key_photo_url column not found for tomograms with reconstruction method: {recon_method}"), True
        
        # Filter out tomograms without images
        related_tomograms = related_tomograms[related_tomograms['key_photo_url'].notna()]
        logger.info(f"Tomograms with images: {len(related_tomograms)}")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_tomograms.to_dict('records')
        
        # If too many items, randomly sample
        if len(related_items) > 100:
            related_items = random.sample(related_items, 100)
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            return html.P(f"No tomograms found for reconstruction method: {recon_method}"), True
        
        # Create the grid gallery of related tomograms
        gallery = create_related_items_grid_gallery(related_items, 'tomogram', f"Tomograms with Reconstruction Method: {recon_method}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.exception(f"Error displaying related tomograms: {str(e)}")
        return html.P(f"Error displaying related tomograms: {str(e)}"), True

# Callback to show a grid gallery of related tomograms for the processing method table
@callback(
    [Output("tomograms-proc-method-related-items", "children"),
     Output("tomograms-proc-method-related-items-collapse", "is_open")],
    [Input("tomograms-proc-method-datatable", "active_cell"),
     Input("tomograms-proc-method-datatable", "data")]
)
def display_tomograms_proc_method_related_items(active_cell, data):
    """
    Display a grid gallery of tomograms for the selected processing method.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related tomograms"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        proc_method = selected_row['processing_method']
        
        logger.info(f"Tomograms Proc Method - Selected method: {proc_method}")
        
        # Fetch all tomograms
        all_tomograms = fetch_tomograms()
        
        # Filter tomograms for the selected processing method
        related_tomograms = all_tomograms[all_tomograms['processing_method'] == proc_method]
        
        logger.info(f"Tomograms Proc Method - Found {len(related_tomograms)} related tomograms for {proc_method}")
        logger.info(f"Tomograms columns: {list(related_tomograms.columns)}")
        
        # Check if key_photo_url exists and is not empty
        if 'key_photo_url' not in related_tomograms.columns:
            logger.error("key_photo_url column not found in tomograms data")
            return html.P(f"Error: key_photo_url column not found for tomograms with processing method: {proc_method}"), True
        
        # Filter out tomograms without images
        related_tomograms = related_tomograms[related_tomograms['key_photo_url'].notna()]
        logger.info(f"Tomograms with images: {len(related_tomograms)}")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_tomograms.to_dict('records')
        
        # If too many items, randomly sample
        if len(related_items) > 100:
            related_items = random.sample(related_items, 100)
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            return html.P(f"No tomograms found for processing method: {proc_method}"), True
        
        # Create the grid gallery of related tomograms
        gallery = create_related_items_grid_gallery(related_items, 'tomogram', f"Tomograms with Processing Method: {proc_method}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.exception(f"Error displaying related tomograms: {str(e)}")
        return html.P(f"Error displaying related tomograms: {str(e)}"), True

# Callback to show a grid gallery of related tomograms for the voxel spacing table
@callback(
    [Output("tomograms-voxel-spacing-related-items", "children"),
     Output("tomograms-voxel-spacing-related-items-collapse", "is_open")],
    [Input("tomograms-voxel-spacing-datatable", "active_cell"),
     Input("tomograms-voxel-spacing-datatable", "data")]
)
def display_tomograms_voxel_spacing_related_items(active_cell, data):
    """
    Display a grid gallery of tomograms for the selected voxel spacing.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related tomograms"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        voxel_spacing = selected_row['voxel_spacing']
        
        logger.info(f"Tomograms Voxel Spacing - Selected spacing: {voxel_spacing}")
        
        # Fetch all tomograms
        all_tomograms = fetch_tomograms()
        
        # Make sure voxel_spacing is numeric and rounded to match display format
        all_tomograms['voxel_spacing'] = pd.to_numeric(all_tomograms['voxel_spacing'], errors='coerce')
        all_tomograms['voxel_spacing_rounded'] = (all_tomograms['voxel_spacing'] * 10).round() / 10
        
        # Filter tomograms with this voxel spacing
        related_tomograms = all_tomograms[all_tomograms['voxel_spacing_rounded'] == float(voxel_spacing)]
        
        logger.info(f"Tomograms Voxel Spacing - Found {len(related_tomograms)} related tomograms for spacing {voxel_spacing}")
        
        # Check if key_photo_url exists and is not empty
        if 'key_photo_url' not in related_tomograms.columns:
            logger.error("key_photo_url column not found in tomograms data")
            return html.P(f"Error: key_photo_url column not found for tomograms with voxel spacing: {voxel_spacing}"), True
        
        # Filter out tomograms without images
        related_tomograms = related_tomograms[related_tomograms['key_photo_url'].notna()]
        logger.info(f"Tomograms with images: {len(related_tomograms)}")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_tomograms.to_dict('records')
        
        # If too many items, randomly sample
        if len(related_items) > 100:
            related_items = random.sample(related_items, 100)
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            return html.P(f"No tomograms found for voxel spacing: {voxel_spacing}"), True
        
        # Create the grid gallery of related tomograms
        gallery = create_related_items_grid_gallery(related_items, 'tomogram', f"Tomograms with Voxel Spacing: {voxel_spacing}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.exception(f"Error displaying related tomograms: {str(e)}")
        return html.P(f"Error displaying related tomograms: {str(e)}"), True

# Callback for reshuffling tomograms added in period gallery
@callback(
    Output("related-tomogram-tomograms-added-in-period-gallery", "children"),
    Input("related-tomogram-tomograms-added-in-period-refresh-button", "n_clicks"),
    State("related-tomogram-tomograms-added-in-period-items-store", "data")
)
def reshuffle_tomograms_added_gallery(n_clicks, stored_items):
    """Reshuffle the tomograms added in period gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling tomograms added gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
    # Create a new shuffled gallery
    selected_items = stored_items.copy()
    random.shuffle(selected_items)
    selected_items = selected_items[:36]  # Limit to 36 items
    
    # Create image cards
    image_cards = []
    grid_size = 6
    
    for item in selected_items:
        # Skip items without required fields
        item_id = item.get('id', '')
        if not item_id:
            continue
            
        image_url = item.get('key_photo_url', '')
        if not image_url:
            continue
            
        # Create caption
        caption = f"Tomogram {item_id}"
        
        # Get link
        run_id = item.get('run_id', '')
        if run_id:
            link = f"{PORTAL_BASE_URL}/runs/{run_id}"
        else:
            link = f"{PORTAL_BASE_URL}/depositions/{item.get('deposition_id', '')}"
            
        # Create card
        image_cards.append(
            dbc.Col(
                html.Div([
                    html.A([
                        html.Img(
                            src=image_url,
                            style={
                                "height": "150px",
                                "objectFit": "cover",
                                "borderRadius": "4px",
                                "width": "100%"
                            }
                        ),
                        html.Div(
                            caption,
                            style={
                                "fontSize": "12px",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "whiteSpace": "nowrap",
                                "maxWidth": "100%",
                                "textAlign": "center",
                                "marginTop": "5px"
                            }
                        )
                    ], 
                    href=link,
                    target="_blank",
                    title=f"View {caption} details in the Data Portal",
                    style={"textDecoration": "none", "color": "inherit"},
                    className="external-link"
                    )
                ],
                className="related-image-card mb-3")
            )
        )
    
    # Fill remaining slots
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

# Callback for reshuffling tomograms up to date gallery
@callback(
    Output("related-tomogram-tomograms-up-to-date-gallery", "children"),
    Input("related-tomogram-tomograms-up-to-date-refresh-button", "n_clicks"),
    State("related-tomogram-tomograms-up-to-date-items-store", "data")
)
def reshuffle_tomograms_cumulative_gallery(n_clicks, stored_items):
    """Reshuffle the tomograms up to date gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling tomograms cumulative gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
    # Create a new shuffled gallery
    selected_items = stored_items.copy()
    random.shuffle(selected_items)
    selected_items = selected_items[:36]  # Limit to 36 items
    
    # Create image cards following the same pattern as above
    # (Code omitted for brevity but follows the same pattern)
    
    # Create image cards
    image_cards = []
    grid_size = 6
    
    for item in selected_items:
        # Skip items without required fields
        item_id = item.get('id', '')
        if not item_id:
            continue
            
        image_url = item.get('key_photo_url', '')
        if not image_url:
            continue
            
        # Create caption
        caption = f"Tomogram {item_id}"
        
        # Get link
        run_id = item.get('run_id', '')
        if run_id:
            link = f"{PORTAL_BASE_URL}/runs/{run_id}"
        else:
            link = f"{PORTAL_BASE_URL}/depositions/{item.get('deposition_id', '')}"
            
        # Create card
        image_cards.append(
            dbc.Col(
                html.Div([
                    html.A([
                        html.Img(
                            src=image_url,
                            style={
                                "height": "150px",
                                "objectFit": "cover",
                                "borderRadius": "4px",
                                "width": "100%"
                            }
                        ),
                        html.Div(
                            caption,
                            style={
                                "fontSize": "12px",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "whiteSpace": "nowrap",
                                "maxWidth": "100%",
                                "textAlign": "center",
                                "marginTop": "5px"
                            }
                        )
                    ], 
                    href=link,
                    target="_blank",
                    title=f"View {caption} details in the Data Portal",
                    style={"textDecoration": "none", "color": "inherit"},
                    className="external-link"
                    )
                ],
                className="related-image-card mb-3")
            )
        )
    
    # Fill remaining slots
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

# Callback for reshuffling tomograms with reconstruction method gallery
@callback(
    Output("related-tomogram-tomograms-with-reconstruction-method-gallery", "children"),
    Input("related-tomogram-tomograms-with-reconstruction-method-refresh-button", "n_clicks"),
    State("related-tomogram-tomograms-with-reconstruction-method-items-store", "data")
)
def reshuffle_tomograms_recon_method_gallery(n_clicks, stored_items):
    """Reshuffle the tomograms with reconstruction method gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling tomograms recon method gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
    # Create image cards
    image_cards = []
    grid_size = 6
    
    # Create a new shuffled gallery
    selected_items = stored_items.copy()
    random.shuffle(selected_items)
    selected_items = selected_items[:36]  # Limit to 36 items
    
    for item in selected_items:
        # Skip items without required fields
        item_id = item.get('id', '')
        if not item_id:
            continue
            
        image_url = item.get('key_photo_url', '')
        if not image_url:
            continue
            
        # Create caption
        caption = f"Tomogram {item_id}"
        
        # Get link
        run_id = item.get('run_id', '')
        if run_id:
            link = f"{PORTAL_BASE_URL}/runs/{run_id}"
        else:
            link = f"{PORTAL_BASE_URL}/depositions/{item.get('deposition_id', '')}"
            
        # Create card
        image_cards.append(
            dbc.Col(
                html.Div([
                    html.A([
                        html.Img(
                            src=image_url,
                            style={
                                "height": "150px",
                                "objectFit": "cover",
                                "borderRadius": "4px",
                                "width": "100%"
                            }
                        ),
                        html.Div(
                            caption,
                            style={
                                "fontSize": "12px",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "whiteSpace": "nowrap",
                                "maxWidth": "100%",
                                "textAlign": "center",
                                "marginTop": "5px"
                            }
                        )
                    ], 
                    href=link,
                    target="_blank",
                    title=f"View {caption} details in the Data Portal",
                    style={"textDecoration": "none", "color": "inherit"},
                    className="external-link"
                    )
                ],
                className="related-image-card mb-3")
            )
        )
    
    # Fill remaining slots
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

# Callback for reshuffling tomograms with processing method gallery
@callback(
    Output("related-tomogram-tomograms-with-processing-method-gallery", "children"),
    Input("related-tomogram-tomograms-with-processing-method-refresh-button", "n_clicks"),
    State("related-tomogram-tomograms-with-processing-method-items-store", "data")
)
def reshuffle_tomograms_proc_method_gallery(n_clicks, stored_items):
    """Reshuffle the tomograms with processing method gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling tomograms proc method gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
    # Create image cards
    image_cards = []
    grid_size = 6
    
    # Create a new shuffled gallery
    selected_items = stored_items.copy()
    random.shuffle(selected_items)
    selected_items = selected_items[:36]  # Limit to 36 items
    
    for item in selected_items:
        # Skip items without required fields
        item_id = item.get('id', '')
        if not item_id:
            continue
            
        image_url = item.get('key_photo_url', '')
        if not image_url:
            continue
            
        # Create caption
        caption = f"Tomogram {item_id}"
        
        # Get link
        run_id = item.get('run_id', '')
        if run_id:
            link = f"{PORTAL_BASE_URL}/runs/{run_id}"
        else:
            link = f"{PORTAL_BASE_URL}/depositions/{item.get('deposition_id', '')}"
            
        # Create card
        image_cards.append(
            dbc.Col(
                html.Div([
                    html.A([
                        html.Img(
                            src=image_url,
                            style={
                                "height": "150px",
                                "objectFit": "cover",
                                "borderRadius": "4px",
                                "width": "100%"
                            }
                        ),
                        html.Div(
                            caption,
                            style={
                                "fontSize": "12px",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "whiteSpace": "nowrap",
                                "maxWidth": "100%",
                                "textAlign": "center",
                                "marginTop": "5px"
                            }
                        )
                    ], 
                    href=link,
                    target="_blank",
                    title=f"View {caption} details in the Data Portal",
                    style={"textDecoration": "none", "color": "inherit"},
                    className="external-link"
                    )
                ],
                className="related-image-card mb-3")
            )
        )
    
    # Fill remaining slots
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

# Callback for reshuffling tomograms with voxel spacing gallery
@callback(
    Output("related-tomogram-tomograms-with-voxel-spacing-gallery", "children"),
    Input("related-tomogram-tomograms-with-voxel-spacing-refresh-button", "n_clicks"),
    State("related-tomogram-tomograms-with-voxel-spacing-items-store", "data")
)
def reshuffle_tomograms_voxel_spacing_gallery(n_clicks, stored_items):
    """Reshuffle the tomograms with voxel spacing gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling tomograms voxel spacing gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
    # Create image cards
    image_cards = []
    grid_size = 6
    
    # Create a new shuffled gallery
    selected_items = stored_items.copy()
    random.shuffle(selected_items)
    selected_items = selected_items[:36]  # Limit to 36 items
    
    for item in selected_items:
        # Skip items without required fields
        item_id = item.get('id', '')
        if not item_id:
            continue
            
        image_url = item.get('key_photo_url', '')
        if not image_url:
            continue
            
        # Create caption
        caption = f"Tomogram {item_id}"
        
        # Get link
        run_id = item.get('run_id', '')
        if run_id:
            link = f"{PORTAL_BASE_URL}/runs/{run_id}"
        else:
            link = f"{PORTAL_BASE_URL}/depositions/{item.get('deposition_id', '')}"
            
        # Create card
        image_cards.append(
            dbc.Col(
                html.Div([
                    html.A([
                        html.Img(
                            src=image_url,
                            style={
                                "height": "150px",
                                "objectFit": "cover",
                                "borderRadius": "4px",
                                "width": "100%"
                            }
                        ),
                        html.Div(
                            caption,
                            style={
                                "fontSize": "12px",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "whiteSpace": "nowrap",
                                "maxWidth": "100%",
                                "textAlign": "center",
                                "marginTop": "5px"
                            }
                        )
                    ], 
                    href=link,
                    target="_blank",
                    title=f"View {caption} details in the Data Portal",
                    style={"textDecoration": "none", "color": "inherit"},
                    className="external-link"
                    )
                ],
                className="related-image-card mb-3")
            )
        )
    
    # Fill remaining slots
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

# Callbacks for SVG downloads
@callback(
    Output(f"tomograms-added-download-svg", "data"),
    Input("tomograms-added-download-svg-button", "n_clicks"),
    State("tomograms-added-plot", "figure"),
    prevent_initial_call=True,
)
def download_tomograms_added_svg(n_clicks, figure):
    """Download the tomograms added chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "tomograms_added")


@callback(
    Output(f"tomograms-cumulative-download-svg", "data"),
    Input("tomograms-cumulative-download-svg-button", "n_clicks"),
    State("tomograms-cumulative-plot", "figure"),
    prevent_initial_call=True,
)
def download_tomograms_cumulative_svg(n_clicks, figure):
    """Download the cumulative tomograms chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "tomograms_cumulative")


@callback(
    Output(f"tomograms-recon-method-download-svg", "data"),
    Input("tomograms-recon-method-download-svg-button", "n_clicks"),
    State("tomograms-recon-method-plot", "figure"),
    prevent_initial_call=True,
)
def download_tomograms_recon_method_svg(n_clicks, figure):
    """Download the tomograms by reconstruction method chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "tomograms_by_recon_method")


@callback(
    Output(f"tomograms-proc-method-download-svg", "data"),
    Input("tomograms-proc-method-download-svg-button", "n_clicks"),
    State("tomograms-proc-method-plot", "figure"),
    prevent_initial_call=True,
)
def download_tomograms_proc_method_svg(n_clicks, figure):
    """Download the tomograms by processing method chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "tomograms_by_proc_method")


@callback(
    Output(f"tomograms-voxel-spacing-download-svg", "data"),
    Input("tomograms-voxel-spacing-download-svg-button", "n_clicks"),
    State("tomograms-voxel-spacing-plot", "figure"),
    prevent_initial_call=True,
)
def download_tomograms_voxel_spacing_svg(n_clicks, figure):
    """Download the tomograms by voxel spacing chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download
    return generate_svg_download(figure, "tomograms_by_voxel_spacing") 