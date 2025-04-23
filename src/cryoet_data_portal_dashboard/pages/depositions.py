"""Depositions page for the dashboard."""
import pandas as pd
from dash import dcc, html, callback, Output, Input, State, dash_table, no_update, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
from datetime import datetime
import logging
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
    create_related_items_links,
    generate_csv_download,
    generate_svg_download
)
from cryoet_data_portal_dashboard.data_utils import (
    fetch_depositions, 
    get_deposition_images,
    get_depositions_for_filtering
)
from cryoet_data_portal_dashboard.cache import cache

logger = logging.getLogger(__name__)

# Get deposition images for the gallery
deposition_images = get_deposition_images()

# Define the layout for the depositions page
layout = dbc.Container(
    [
        dcc.Location(id="depositions-url", refresh=False),  # Add location component
        html.H2("Depositions", className="mb-3"),  # Changed from H1 to H2 and removed "Dashboard"
        
        # Image Gallery
        create_auto_scrolling_image_gallery(
            deposition_images, 
            "Example Depositions"
        ),
        
        # Interactive Table Info Alert
        dbc.Alert(
            [
                html.H5("Interactive Table Instructions", className="alert-heading"),
                html.P(
                    "The tables below are interactive. Click on any row to highlight it and view related depositions "
                    "data. A panel with links to related items will appear below the chart. You can filter data using "
                    "the date range selectors."
                ),
            ],
            color="info",
            className="mb-4",
        ),
        
        # Card 1: Number of depositions added per month
        create_card(
            title="Number of Depositions Added Per Month",
            table_component=html.Div(
                [
                    create_date_range_selector("depositions-added"),
                    html.Div(id="depositions-added-table"),
                ]
            ),
            plot_component=dcc.Graph(id="depositions-added-plot"),
            id_prefix="depositions-added"
        ),
        
        # Card 2: Cumulative number of depositions per month
        create_card(
            title="Cumulative Number of Depositions",
            table_component=html.Div(
                [
                    create_date_range_selector("depositions-cumulative"),
                    html.Div(id="depositions-cumulative-table"),
                ]
            ),
            plot_component=dcc.Graph(id="depositions-cumulative-plot"),
            id_prefix="depositions-cumulative"
        ),
    ],
    fluid=True,
    className="py-3",
)


# Callback for depositions added per month
@callback(
    [Output("depositions-added-table", "children"),
     Output("depositions-added-plot", "figure")],
    [Input("depositions-added-date-range", "start_date"),
     Input("depositions-added-date-range", "end_date"),
     Input("depositions-added-interval", "value"),
     Input("depositions-added-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_depositions_added(start_date, end_date, interval, n_clicks):
    # Fetch data
    df = fetch_depositions()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Create the table with cell selection
    table = dash_table.DataTable(
        id='depositions-added-datatable',
        data=grouped_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Depositions Added", "id": "count"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
        # Enable highlighting of entire row when a cell is clicked
        style_data_conditional=[
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                'border': '1px solid blue'
            }
        ],
        # Make rows clickable
        css=[{
            'selector': 'tr',
            'rule': 'cursor: pointer'
        }],
    )
    
    # Create the plot
    fig = create_line_chart(
        grouped_df, 
        date_col, 
        'count', 
        "Depositions Added Over Time",
        labels={"count": "Number of Depositions", date_col: "Date"}
    )
    
    return table, fig


# Callback to show related depositions when a cell is clicked
@callback(
    [Output("depositions-added-related-items", "children"),
     Output("depositions-added-related-items-collapse", "is_open")],
    [Input("depositions-added-datatable", "active_cell"),
     Input("depositions-added-datatable", "data")]
)
def display_depositions_added_related_items(active_cell, data):
    """Display links to depositions related to the selected table row.
    
    This callback is triggered when a user clicks on a cell in the depositions table.
    It identifies the selected row, extracts the date information, and finds all
    depositions that were added in that specific time period (e.g., month).
    
    The links displayed include the deposition ID and title, and they open the
    corresponding deposition page in the CryoET Data Portal when clicked.
    
    When no row is selected, the related items section is hidden. When a row
    is selected, the related items section appears below the plot.
    
    Args:
        active_cell (dict): Information about the currently active (clicked) cell
        data (list): The data displayed in the table
        
    Returns:
        tuple: (related_items_component, is_collapse_open)
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related depositions"), False
    
    # Get the row index from the active cell
    row_idx = active_cell['row']
    
    # Get the selected row data
    selected_row = data[row_idx]
    selected_date = selected_row['deposition_date']
    
    logger.info(f"Selected row data: {selected_row}")
    logger.info(f"Selected date: {selected_date}")
    
    # Fetch all depositions with pre-formatted date columns
    all_depositions = get_depositions_for_filtering()
    logger.info(f"Total depositions: {len(all_depositions)}")
    
    # Convert the selected date string to a datetime object for comparison
    selected_date = pd.to_datetime(selected_date)
    logger.info(f"Converted selected date: {selected_date}")
    
    # Extract year and month from selected date for filtering
    selected_year = selected_date.year
    selected_month = selected_date.month
    selected_year_month = selected_date.strftime('%Y-%m')
    
    logger.info(f"Filtering for year: {selected_year}, month: {selected_month}")
    
    # Filter using string comparison to avoid timezone issues
    related_depositions = all_depositions[
        all_depositions['deposition_date'].dt.strftime('%Y-%m') == selected_year_month
    ]
    
    logger.info(f"Found {len(related_depositions)} related depositions for {selected_year_month}")
    
    # Convert to list of dicts for the link creation function
    related_items = related_depositions.to_dict('records')
    
    # If still no items, provide a message
    if not related_items or len(related_items) == 0:
        logger.info("No related items found for the selected date")
        return html.P(f"No depositions found for {selected_date.strftime('%B %Y')}"), True
    
    # Create links to the related depositions
    links = create_related_items_links(related_items, 'deposition')
    
    # Return the links and set is_open to True
    return links, True


# Callback for cumulative depositions
@callback(
    [Output("depositions-cumulative-table", "children"),
     Output("depositions-cumulative-plot", "figure")],
    [Input("depositions-cumulative-date-range", "start_date"),
     Input("depositions-cumulative-date-range", "end_date"),
     Input("depositions-cumulative-interval", "value"),
     Input("depositions-cumulative-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_depositions_cumulative(start_date, end_date, interval, n_clicks):
    # Fetch data
    df = fetch_depositions()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Calculate cumulative counts
    cumulative_df = calculate_cumulative(grouped_df, date_col)
    
    # Create the table with cell selection
    table = dash_table.DataTable(
        id='depositions-cumulative-datatable',
        data=cumulative_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Cumulative Depositions", "id": "cumulative"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={'fontWeight': 'bold'},
        # Enable highlighting of entire row when a cell is clicked
        style_data_conditional=[
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                'border': '1px solid blue'
            }
        ],
        # Make rows clickable
        css=[{
            'selector': 'tr',
            'rule': 'cursor: pointer'
        }],
    )
    
    # Create the plot
    fig = create_line_chart(
        cumulative_df, 
        date_col, 
        'cumulative', 
        "Cumulative Number of Depositions Over Time",
        labels={"cumulative": "Cumulative Number of Depositions", date_col: "Date"}
    )
    
    return table, fig


# Callback to show related depositions for the cumulative view
@callback(
    [Output("depositions-cumulative-related-items", "children"),
     Output("depositions-cumulative-related-items-collapse", "is_open")],
    [Input("depositions-cumulative-datatable", "active_cell"),
     Input("depositions-cumulative-datatable", "data")]
)
def display_depositions_cumulative_related_items(active_cell, data):
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related depositions"), False
    
    # Get the row index from the active cell
    row_idx = active_cell['row']
    
    # Get the selected row data
    selected_row = data[row_idx]
    selected_date = selected_row['deposition_date']
    
    logger.info(f"Cumulative - Selected row data: {selected_row}")
    logger.info(f"Cumulative - Selected date: {selected_date}")
    
    # Fetch all depositions with pre-formatted date columns
    all_depositions = get_depositions_for_filtering()
    logger.info(f"Cumulative - Total depositions: {len(all_depositions)}")
    
    # Convert the selected date string to a datetime object for comparison
    selected_date = pd.to_datetime(selected_date)
    logger.info(f"Cumulative - Converted selected date: {selected_date}")
    
    # For cumulative data, we want all depositions up to and including the selected date
    # Handle timezone compatibility by comparing the dates using string representation (YYYY-MM-DD)
    selected_date_str = selected_date.strftime('%Y-%m-%d')
    
    # Use date string comparison to avoid timezone issues
    related_depositions = all_depositions[
        all_depositions['deposition_date'].dt.strftime('%Y-%m-%d') <= selected_date_str
    ]
    
    logger.info(f"Cumulative - Found {len(related_depositions)} related depositions up to {selected_date}")
    
    # Convert to list of dicts for the link creation function
    related_items = related_depositions.to_dict('records')
    
    # If still no items, provide a message
    if not related_items or len(related_items) == 0:
        logger.info("Cumulative - No related items found for the selected date")
        return html.P(f"No depositions found up to {selected_date.strftime('%B %Y')}"), True
    
    # Create links to the related depositions
    links = create_related_items_links(related_items, 'deposition')
    
    # Return the links and set is_open to True
    return links, True


# Callback for refreshing the gallery
@callback(
    Output("example-depositions-gallery", "children"),
    Input("example-depositions-refresh-button", "n_clicks")
)
def refresh_deposition_images(n_clicks):
    """
    Refresh the deposition images gallery when the reshuffle button is clicked.
    """
    if n_clicks is None:
        return no_update
    
    # Get fresh random images, using n_clicks as a cache buster
    images = get_deposition_images(cache_buster=n_clicks)
    logger.info(f"Got {len(images)} images from get_deposition_images(), cache_buster={n_clicks}")
    
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


# Callbacks for CSV downloads
@callback(
    Output("depositions-added-download-csv", "data"),
    Input("depositions-added-download-button", "n_clicks"),
    State("depositions-added-datatable", "data"),
    prevent_initial_call=True,
)
def download_depositions_added_csv(n_clicks, data):
    """Download the depositions added table data as CSV"""
    if n_clicks is None or not data:
        return no_update
    
    # Convert table data to dataframe
    df = pd.DataFrame(data)
    
    # Generate CSV download with appropriate filename
    return generate_csv_download(df, "depositions_added")


@callback(
    Output("depositions-cumulative-download-csv", "data"),
    Input("depositions-cumulative-download-button", "n_clicks"),
    State("depositions-cumulative-datatable", "data"),
    prevent_initial_call=True,
)
def download_depositions_cumulative_csv(n_clicks, data):
    """Download the cumulative depositions table data as CSV"""
    if n_clicks is None or not data:
        return no_update
    
    # Convert table data to dataframe
    df = pd.DataFrame(data)
    
    # Generate CSV download with appropriate filename
    return generate_csv_download(df, "depositions_cumulative")


# Callbacks for SVG downloads
@callback(
    Output(f"depositions-added-download-svg", "data"),
    Input("depositions-added-download-svg-button", "n_clicks"),
    State("depositions-added-plot", "figure"),
    prevent_initial_call=True,
)
def download_depositions_added_svg(n_clicks, figure):
    """Download the depositions added chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Convert the figure dict to a Figure object
    import plotly.io as pio
    
    # Generate SVG download
    return generate_svg_download(figure, "depositions_added")


@callback(
    Output(f"depositions-cumulative-download-svg", "data"),
    Input("depositions-cumulative-download-svg-button", "n_clicks"),
    State("depositions-cumulative-plot", "figure"),
    prevent_initial_call=True,
)
def download_depositions_cumulative_svg(n_clicks, figure):
    """Download the cumulative depositions chart as SVG"""
    if n_clicks is None or not figure:
        return no_update
    
    # Generate SVG download directly from the figure dict
    return generate_svg_download(figure, "depositions_cumulative") 