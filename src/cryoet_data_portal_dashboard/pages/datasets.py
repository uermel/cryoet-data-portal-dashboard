"""Datasets page for the dashboard."""
import pandas as pd
from dash import dcc, html, callback, Output, Input, State, dash_table, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
from datetime import datetime
import logging

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
    generate_csv_download
)
from cryoet_data_portal_dashboard.data_utils import (
    fetch_datasets,
    get_datasets_by_sample_type,
    get_datasets_by_organism,
    get_dataset_images,
    get_datasets_for_filtering
)
from cryoet_data_portal_dashboard.cache import cache

logger = logging.getLogger(__name__)

# Get dataset images for the gallery
dataset_images = get_dataset_images()

# Define the layout for the datasets page
layout = dbc.Container(
    [
        dcc.Location(id="datasets-url", refresh=False),  # Add location component to provide input for callbacks
        html.H2("Datasets", className="mb-3"),  # Changed from H1 to H2 and removed "Dashboard"
        
        # Image Gallery
        create_auto_scrolling_image_gallery(
            dataset_images, 
            "Example Datasets"
        ),
        
        # Interactive Table Info Alert
        dbc.Alert(
            [
                html.H5("Interactive Table Instructions", className="alert-heading"),
                html.P(
                    "The tables below are interactive. Click on any row to highlight it and view related datasets "
                    "data. A panel with links to related items will appear below the chart. You can filter data using "
                    "the date range selectors. For sample type and organism tables, clicking on a row will show all "
                    "datasets of that specific type."
                ),
            ],
            color="info",
            className="mb-4",
        ),
        
        # Card 1: Number of datasets added per month
        create_card(
            title="Number of Datasets Added Per Month",
            table_component=html.Div(
                [
                    create_date_range_selector("datasets-added"),
                    html.Div(id="datasets-added-table"),
                ]
            ),
            plot_component=dcc.Graph(id="datasets-added-plot"),
            id_prefix="datasets-added"
        ),
        
        # Card 2: Cumulative number of datasets per month
        create_card(
            title="Cumulative Number of Datasets",
            table_component=html.Div(
                [
                    create_date_range_selector("datasets-cumulative"),
                    html.Div(id="datasets-cumulative-table"),
                ]
            ),
            plot_component=dcc.Graph(id="datasets-cumulative-plot"),
            id_prefix="datasets-cumulative"
        ),
        
        # Card 3: Datasets per sample type
        create_card(
            title="Datasets by Sample Type",
            table_component=html.Div(id="datasets-sample-type-table"),
            plot_component=dcc.Graph(id="datasets-sample-type-plot"),
            id_prefix="datasets-sample-type"
        ),
        
        # Card 4: Datasets per organism name
        create_card(
            title="Datasets by Organism",
            table_component=html.Div(id="datasets-organism-table"),
            plot_component=dcc.Graph(id="datasets-organism-plot"),
            id_prefix="datasets-organism"
        ),
    ],
    fluid=True,
    className="py-3",
)


# Callback for datasets added per month
@callback(
    [Output("datasets-added-table", "children"),
     Output("datasets-added-plot", "figure")],
    [Input("datasets-added-date-range", "start_date"),
     Input("datasets-added-date-range", "end_date"),
     Input("datasets-added-interval", "value"),
     Input("datasets-added-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_datasets_added(start_date, end_date, interval, n_clicks):
    """
    Update the Datasets Added table and plot based on date range and interval selection.
    
    This callback fetches datasets data, filters it by the selected date range,
    groups it by the specified interval, and creates an interactive table and line chart.
    The table allows users to click on rows to view datasets added during that time period.
    
    Args:
        start_date (str): Start date for filtering
        end_date (str): End date for filtering
        interval (str): Interval for grouping ('day', 'week', 'month', 'year')
        n_clicks (int): Number of times refresh button has been clicked
        
    Returns:
        tuple: (DataTable component, Plotly figure)
    """
    # Fetch data
    df = fetch_datasets()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Format date column for table display (already formatted as date in group_by_interval)
    table_data = grouped_df.to_dict('records')
    
    # Create the table with interactive features
    table = dash_table.DataTable(
        id='datasets-added-datatable',  # Add ID for callback
        data=table_data,
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Datasets Added", "id": "count"}
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
        "Datasets Added Over Time",
        labels={"count": "Number of Datasets", date_col: "Date"}
    )
    
    return table, fig


# Callback for cumulative datasets
@callback(
    [Output("datasets-cumulative-table", "children"),
     Output("datasets-cumulative-plot", "figure")],
    [Input("datasets-cumulative-date-range", "start_date"),
     Input("datasets-cumulative-date-range", "end_date"),
     Input("datasets-cumulative-interval", "value"),
     Input("datasets-cumulative-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_datasets_cumulative(start_date, end_date, interval, n_clicks):
    """
    Update the Cumulative Datasets table and plot based on date range and interval selection.
    
    This callback fetches datasets data, filters it by the selected date range,
    groups it by the specified interval, calculates cumulative counts, and creates
    an interactive table and line chart. The table allows users to click on rows
    to view datasets added up to that time period.
    
    Args:
        start_date (str): Start date for filtering
        end_date (str): End date for filtering
        interval (str): Interval for grouping ('day', 'week', 'month', 'year')
        n_clicks (int): Number of times refresh button has been clicked
        
    Returns:
        tuple: (DataTable component, Plotly figure)
    """
    # Fetch data
    df = fetch_datasets()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Calculate cumulative
    cumulative_df = calculate_cumulative(grouped_df, date_col)
    
    # Create the table with interactive features
    table = dash_table.DataTable(
        id='datasets-cumulative-datatable',  # Add ID for callback
        data=cumulative_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Datasets Added", "id": "count"},
            {"name": "Cumulative Datasets", "id": "cumulative"}
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
        "Cumulative Datasets Over Time",
        labels={"cumulative": "Total Number of Datasets", date_col: "Date"}
    )
    
    return table, fig


# Callback for datasets by sample type
@callback(
    [Output("datasets-sample-type-table", "children"),
     Output("datasets-sample-type-plot", "figure")],
    [Input("datasets-url", "pathname"),
     Input("datasets-sample-type-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_datasets_by_sample_type(pathname, n_clicks):
    """
    Update the Datasets by Sample Type table and plot.
    
    This callback fetches datasets grouped by sample type and creates an interactive
    table and bar chart. The table allows users to click on rows to view all datasets
    with the selected sample type.
    
    Args:
        pathname (str): Current page URL path (not used but required for Input)
        n_clicks (int): Number of times refresh button has been clicked
        
    Returns:
        tuple: (DataTable component, Plotly figure)
    """
    # Get data
    df = get_datasets_by_sample_type()
    
    # Create the table with cell selection
    table = dash_table.DataTable(
        id='datasets-sample-type-datatable',
        data=df.to_dict('records'),
        columns=[
            {"name": "Sample Type", "id": "sample_type"},
            {"name": "Number of Datasets", "id": "count"}
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
    fig = create_bar_chart(
        df, 
        'sample_type', 
        'count', 
        "Number of Datasets by Sample Type",
        labels={"count": "Number of Datasets", "sample_type": "Sample Type"}
    )
    
    return table, fig


# Callback to show related datasets for sample type
@callback(
    [Output("datasets-sample-type-related-items", "children"),
     Output("datasets-sample-type-related-items-collapse", "is_open")],
    [Input("datasets-sample-type-datatable", "active_cell"),
     Input("datasets-sample-type-datatable", "data")]
)
def display_datasets_sample_type_related_items(active_cell, data):
    """
    Display links to datasets with the selected sample type.
    
    This callback is triggered when a user clicks on a cell in the datasets by sample type table.
    It identifies the selected row's sample type, retrieves all datasets with that sample type,
    and displays links to these datasets in the related items section.
    
    Args:
        active_cell (dict): Information about the clicked cell including row and column indices
        data (list): The data displayed in the table as a list of dictionaries
        
    Returns:
        tuple: (Related items component, Boolean indicating if collapse is open)
    """
    # If no cell is clicked, hide the collapse
    if active_cell is None or not data:
        return html.P("Click on a table cell to see related datasets"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        sample_type = selected_row.get('sample_type')
        
        if not sample_type:
            logger.error("No sample_type found in selected row")
            return html.P("Error: Could not find sample type information in the selected row"), True
        
        logger.info(f"Sample Type - Selected row data: {selected_row}")
        logger.info(f"Sample Type - Selected sample type: {sample_type}")
        
        # Fetch all datasets
        all_datasets = fetch_datasets()
        logger.info(f"Sample Type - Total datasets: {len(all_datasets)}")
        
        # Filter datasets with the selected sample type
        related_datasets = all_datasets[all_datasets['sample_type'] == sample_type]
        
        logger.info(f"Sample Type - Found {len(related_datasets)} related datasets with sample type {sample_type}")
        
        # Convert to list of dicts for the link creation function
        related_items = related_datasets.to_dict('records')
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            logger.info(f"Sample Type - No related items found for sample type {sample_type}")
            return html.P(f"No datasets found for sample type '{sample_type}'"), True
        
        # Create links to the related datasets
        links = create_related_items_links(related_items, 'dataset')
        
        # Return the links and set is_open to True
        return links, True
    
    except Exception as e:
        logger.error(f"Error in display_datasets_sample_type_related_items: {str(e)}")
        return html.P(f"An error occurred: {str(e)}"), True


# Callback for datasets by organism
@callback(
    [Output("datasets-organism-table", "children"),
     Output("datasets-organism-plot", "figure")],
    [Input("datasets-url", "pathname"),
     Input("datasets-organism-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_datasets_by_organism(pathname, n_clicks):
    """
    Update the Datasets by Organism table and plot.
    
    This callback fetches datasets grouped by organism and creates an interactive
    table and bar chart. The table allows users to click on rows to view all datasets
    with the selected organism.
    
    Args:
        pathname (str): Current page URL path (not used but required for Input)
        n_clicks (int): Number of times refresh button has been clicked
        
    Returns:
        tuple: (DataTable component, Plotly figure)
    """
    # Get data
    df = get_datasets_by_organism()
    
    # Create the table with interactive features
    table = dash_table.DataTable(
        id='datasets-organism-datatable',  # Add ID for callback
        data=df.to_dict('records'),
        columns=[
            {"name": "Organism", "id": "organism_name"},
            {"name": "Count", "id": "count"}
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
    fig = create_bar_chart(
        df, 
        'organism_name', 
        'count', 
        "Datasets by Organism",
        labels={"count": "Number of Datasets", "organism_name": "Organism"}
    )
    
    return table, fig


# Callback for refreshing the gallery
@callback(
    Output("example-datasets-gallery", "children"),
    Input("example-datasets-refresh-button", "n_clicks")
)
def refresh_dataset_images(n_clicks):
    """
    Refresh the dataset images gallery when the reshuffle button is clicked.
    """
    if n_clicks is None:
        return no_update
    
    # Get fresh random images, using n_clicks as a cache buster
    images = get_dataset_images(cache_buster=n_clicks)
    logger.info(f"Got {len(images)} images from get_dataset_images(), cache_buster={n_clicks}")
    
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


# Callback to show related datasets for added datasets table
@callback(
    [Output("datasets-added-related-items", "children"),
     Output("datasets-added-related-items-collapse", "is_open")],
    [Input("datasets-added-datatable", "active_cell"),
     Input("datasets-added-datatable", "data")]
)
def display_datasets_added_related_items(active_cell, data):
    """
    Display links to datasets added during the selected time period.
    
    This callback is triggered when a user clicks on a cell in the datasets added table.
    It identifies the selected row's date, retrieves all datasets added in that specific
    time period (e.g., month), and displays links to these datasets in the related items section.
    
    The links displayed include the dataset ID and title, and they open the corresponding
    dataset page in the CryoET Data Portal when clicked.
    
    Args:
        active_cell (dict): Information about the clicked cell including row and column indices
        data (list): The data displayed in the table as a list of dictionaries
        
    Returns:
        tuple: (Related items component, Boolean indicating if collapse is open)
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related datasets"), False
    
    # Get the row index from the active cell
    row_idx = active_cell['row']
    
    # Get the selected row data
    selected_row = data[row_idx]
    selected_date = selected_row['deposition_date']
    
    logger.info(f"Datasets Added - Selected row data: {selected_row}")
    logger.info(f"Datasets Added - Selected date: {selected_date}")
    
    # Fetch all datasets with pre-formatted date columns
    all_datasets = get_datasets_for_filtering()
    logger.info(f"Datasets Added - Total datasets: {len(all_datasets)}")
    
    # Convert the selected date string to a datetime object for comparison
    selected_date = pd.to_datetime(selected_date)
    logger.info(f"Datasets Added - Converted selected date: {selected_date}")
    
    # Extract year and month from selected date for filtering
    selected_year = selected_date.year
    selected_month = selected_date.month
    selected_year_month = selected_date.strftime('%Y-%m')
    
    logger.info(f"Datasets Added - Filtering for year: {selected_year}, month: {selected_month}")
    
    # Filter using the year_month column to find all datasets from that month
    related_datasets = all_datasets[all_datasets['year_month'] == selected_year_month]
    
    logger.info(f"Datasets Added - Found {len(related_datasets)} related datasets for {selected_year_month}")
    
    # Convert to list of dicts for the link creation function
    related_items = related_datasets.to_dict('records')
    
    # If no items, provide a message
    if not related_items or len(related_items) == 0:
        logger.info(f"Datasets Added - No related items found for date {selected_year_month}")
        return html.P(f"No datasets found for {selected_year_month}"), True
    
    # Create links to the related datasets
    links = create_related_items_links(related_items, 'dataset')
    
    # Return the links and set is_open to True
    return links, True


# Callback to show related datasets for cumulative datasets table
@callback(
    [Output("datasets-cumulative-related-items", "children"),
     Output("datasets-cumulative-related-items-collapse", "is_open")],
    [Input("datasets-cumulative-datatable", "active_cell"),
     Input("datasets-cumulative-datatable", "data")]
)
def display_datasets_cumulative_related_items(active_cell, data):
    """
    Display links to datasets added up to the selected time period.
    
    This callback is triggered when a user clicks on a cell in the cumulative datasets table.
    It identifies the selected row's date, retrieves all datasets added up to and including 
    that date, and displays links to these datasets in the related items section.
    
    The links displayed include the dataset ID and title, and they open the corresponding
    dataset page in the CryoET Data Portal when clicked.
    
    Args:
        active_cell (dict): Information about the clicked cell including row and column indices
        data (list): The data displayed in the table as a list of dictionaries
        
    Returns:
        tuple: (Related items component, Boolean indicating if collapse is open)
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related datasets"), False
    
    # Get the row index from the active cell
    row_idx = active_cell['row']
    
    # Get the selected row data
    selected_row = data[row_idx]
    selected_date = selected_row['deposition_date']
    
    logger.info(f"Datasets Cumulative - Selected row data: {selected_row}")
    logger.info(f"Datasets Cumulative - Selected date: {selected_date}")
    
    # Fetch all datasets with pre-formatted date columns
    all_datasets = get_datasets_for_filtering()
    logger.info(f"Datasets Cumulative - Total datasets: {len(all_datasets)}")
    
    # Convert the selected date string to a datetime object for comparison
    selected_date = pd.to_datetime(selected_date)
    logger.info(f"Datasets Cumulative - Converted selected date: {selected_date}")
    
    # Extract year and month from selected date for filtering
    selected_year = selected_date.year
    selected_month = selected_date.month
    selected_year_month = selected_date.strftime('%Y-%m')
    
    logger.info(f"Datasets Cumulative - Filtering for dates up to year: {selected_year}, month: {selected_month}")
    
    # For cumulative view, we want all datasets up to and including the selected date
    # Use year_month for efficient filtering
    related_datasets = all_datasets[
        (all_datasets['year'] < selected_year) | 
        ((all_datasets['year'] == selected_year) & (all_datasets['month'] <= selected_month))
    ]
    
    logger.info(f"Datasets Cumulative - Found {len(related_datasets)} related datasets up to {selected_year_month}")
    
    # Convert to list of dicts for the link creation function
    related_items = related_datasets.to_dict('records')
    
    # If no items, provide a message
    if not related_items or len(related_items) == 0:
        logger.info(f"Datasets Cumulative - No related items found up to date {selected_year_month}")
        return html.P(f"No datasets found up to {selected_year_month}"), True
    
    # Create links to the related datasets
    links = create_related_items_links(related_items, 'dataset')
    
    # Return the links and set is_open to True
    return links, True


# Callback to show related datasets for organism table
@callback(
    [Output("datasets-organism-related-items", "children"),
     Output("datasets-organism-related-items-collapse", "is_open")],
    [Input("datasets-organism-datatable", "active_cell"),
     Input("datasets-organism-datatable", "data")]
)
def display_datasets_organism_related_items(active_cell, data):
    """
    Display links to datasets with the selected organism.
    
    This callback is triggered when a user clicks on a cell in the datasets by organism table.
    It identifies the selected row's organism, retrieves all datasets with that organism,
    and displays links to these datasets in the related items section.
    
    Args:
        active_cell (dict): Information about the clicked cell including row and column indices
        data (list): The data displayed in the table as a list of dictionaries
        
    Returns:
        tuple: (Related items component, Boolean indicating if collapse is open)
    """
    # If no cell is clicked, hide the collapse
    if active_cell is None or not data:
        return html.P("Click on a table cell to see related datasets"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        organism_name = selected_row.get('organism_name')
        
        if not organism_name:
            logger.error("No organism_name found in selected row")
            return html.P("Error: Could not find organism information in the selected row"), True
        
        logger.info(f"Organism - Selected row data: {selected_row}")
        logger.info(f"Organism - Selected organism: {organism_name}")
        
        # Fetch all datasets
        all_datasets = fetch_datasets()
        logger.info(f"Organism - Total datasets: {len(all_datasets)}")
        
        # Filter datasets with the selected organism
        related_datasets = all_datasets[all_datasets['organism_name'] == organism_name]
        
        logger.info(f"Organism - Found {len(related_datasets)} related datasets with organism {organism_name}")
        
        # Convert to list of dicts for the link creation function
        related_items = related_datasets.to_dict('records')
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            logger.info(f"Organism - No related items found for organism {organism_name}")
            return html.P(f"No datasets found for organism '{organism_name}'"), True
        
        # Create links to the related datasets
        links = create_related_items_links(related_items, 'dataset')
        
        # Return the links and set is_open to True
        return links, True
    
    except Exception as e:
        logger.error(f"Error in display_datasets_organism_related_items: {str(e)}")
        return html.P(f"An error occurred: {str(e)}"), True


# Callbacks for CSV downloads
@callback(
    Output("datasets-added-download-csv", "data"),
    Input("datasets-added-download-button", "n_clicks"),
    State("datasets-added-datatable", "data"),
    prevent_initial_call=True,
)
def download_datasets_added_csv(n_clicks, data):
    """Download the datasets added table data as CSV"""
    if n_clicks is None or not data:
        return no_update
    
    # Convert table data to dataframe
    df = pd.DataFrame(data)
    
    # Generate CSV download with appropriate filename
    return generate_csv_download(df, "datasets_added")


@callback(
    Output("datasets-cumulative-download-csv", "data"),
    Input("datasets-cumulative-download-button", "n_clicks"),
    State("datasets-cumulative-datatable", "data"),
    prevent_initial_call=True,
)
def download_datasets_cumulative_csv(n_clicks, data):
    """Download the cumulative datasets table data as CSV"""
    if n_clicks is None or not data:
        return no_update
    
    # Convert table data to dataframe
    df = pd.DataFrame(data)
    
    # Generate CSV download with appropriate filename
    return generate_csv_download(df, "datasets_cumulative")


@callback(
    Output("datasets-sample-type-download-csv", "data"),
    Input("datasets-sample-type-download-button", "n_clicks"),
    State("datasets-sample-type-datatable", "data"),
    prevent_initial_call=True,
)
def download_datasets_sample_type_csv(n_clicks, data):
    """Download the datasets by sample type table data as CSV"""
    if n_clicks is None or not data:
        return no_update
    
    # Convert table data to dataframe
    df = pd.DataFrame(data)
    
    # Generate CSV download with appropriate filename
    return generate_csv_download(df, "datasets_by_sample_type")


@callback(
    Output("datasets-organism-download-csv", "data"),
    Input("datasets-organism-download-button", "n_clicks"),
    State("datasets-organism-datatable", "data"),
    prevent_initial_call=True,
)
def download_datasets_organism_csv(n_clicks, data):
    """Download the datasets by organism table data as CSV"""
    if n_clicks is None or not data:
        return no_update
    
    # Convert table data to dataframe
    df = pd.DataFrame(data)
    
    # Generate CSV download with appropriate filename
    return generate_csv_download(df, "datasets_by_organism") 