"""Shared components for the dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from cryoet_data_portal import Client
from datetime import datetime, timedelta
import numpy as np
import logging
import random
import io
import base64
from plotly.io import to_image
import json

# Import PORTAL_BASE_URL
from cryoet_data_portal_dashboard.data_utils import PORTAL_BASE_URL

# Initialize API client
client = Client()

# Initialize logger
logger = logging.getLogger(__name__)


def create_graph(figure, id):
    """Create a graph component with the figure and properly apply configuration.
    
    Args:
        figure (plotly.graph_objects.Figure): The figure to display
        id (str): The ID for the graph component
        
    Returns:
        dash component: A dcc.Graph component with the figure and configuration
    """
    return dcc.Graph(
        id=id,
        figure=figure,
        config={
            'displaylogo': False,
            'responsive': True
        }
    )


def create_card(title, table_component, plot_component, id_prefix):
    """Create a card with a title, table, and plot, including a loading indicator and refresh button.

    This card includes an interactive data table that allows users to click on any row to view
    related items. When a row is clicked, the entire row is highlighted, and a collapsible panel
    appears below the plot showing links to the related items (such as depositions, datasets, etc.).

    The table's styling includes:
    - Row highlighting on hover and click
    - Zebra striping for better readability
    - Entire row highlighting when any cell in the row is clicked

    Args:
        title (str): Title of the card
        table_component (dash component): The table component to display on the left
        plot_component (dash component): The plot component to display on the right
        id_prefix (str): Prefix to use for IDs of components within the card

    Returns:
        dash component: A card with table, plot, and related items section
    """
    # If plot_component is a figure (not a dcc.Graph), wrap it in create_graph
    if not isinstance(plot_component, dcc.Graph) and not isinstance(plot_component, html.Div) and not isinstance(plot_component, dcc.Loading):
        plot_id = f"{id_prefix}-plot"
        plot_component = create_graph(plot_component, plot_id)
    
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(html.H4(title), width=6),
                        dbc.Col(
                            html.Div([
                                create_download_buttons(id_prefix, title.lower().replace(' ', '_')),
                                dbc.Button(
                                    [html.I(className="fas fa-sync-alt mr-2"), " Refresh"],
                                    id=f"{id_prefix}-refresh-button",
                                    color="primary",
                                    outline=True,
                                    size="sm",
                                    className="float-end ml-2",
                                    title="Refresh data",
                                    n_clicks=0,
                                ),
                            ], className="d-flex justify-content-end"),
                            width=6,
                            className="d-flex align-items-center justify-content-end",
                        ),
                    ]
                )
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Loading(id=f"{id_prefix}-table-loading", type="circle", children=table_component),
                                width=6,
                                className="h-100",
                            ),
                            dbc.Col(
                                [
                                    dcc.Loading(id=f"{id_prefix}-plot-loading", type="circle", children=plot_component),
                                    # Add related items collapse directly under the plot
                                    dbc.Collapse(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H5("Related Items", className="card-title"),
                                                    html.Div(
                                                        id=f"{id_prefix}-related-items",
                                                        # Removed maxHeight and overflowY to allow full expansion
                                                    ),
                                                ]
                                            )
                                        ),
                                        id=f"{id_prefix}-related-items-collapse",
                                        is_open=False,
                                    ),
                                ],
                                width=6,
                                className="h-100",
                            ),
                        ]
                    ),
                ]
            ),
        ],
        className="mb-4",
        style={"overflow": "visible"},  # Allow overflow for related items
    )


def create_date_range_selector(id_prefix):
    """Create date range selector controls."""
    current_date = datetime.now()
    # Set start date to January 1, 2023
    start_date = datetime(2023, 1, 1).date()

    return html.Div(
        [
            html.Div(
                [
                    html.Label("Date Range:", style={"fontWeight": "bold", "marginRight": "15px"}),
                    dcc.DatePickerRange(
                        id=f"{id_prefix}-date-range",
                        start_date=start_date,
                        end_date=current_date.date(),
                        display_format="YYYY-MM-DD",
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "marginBottom": "15px"},
            ),
            html.Div(
                [
                    html.Label("Interval:", style={"fontWeight": "bold", "marginRight": "15px"}),
                    dcc.RadioItems(
                        id=f"{id_prefix}-interval",
                        options=[
                            {"label": "Daily", "value": "D"},
                            {"label": "Weekly", "value": "W"},
                            {"label": "Monthly", "value": "ME"},
                            {"label": "Quarterly", "value": "QE"},
                            {"label": "Yearly", "value": "YE"},
                        ],
                        value="ME",
                        inline=True,
                        inputStyle={"marginRight": "5px"},
                        labelStyle={"marginRight": "20px"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
        ],
        className="mb-4 p-3 bg-light rounded",
    )


def filter_by_date_range(df, date_column, start_date, end_date):
    """Filter DataFrame by date range."""
    # Create a copy to avoid modifying the original
    filtered_df = df.copy()

    # Skip filtering if no date range is provided
    if not start_date or not end_date:
        return filtered_df

    # Ensure the date column is datetime type
    if not pd.api.types.is_datetime64_any_dtype(filtered_df[date_column]):
        filtered_df[date_column] = pd.to_datetime(filtered_df[date_column])

    # Check if the datetime column has timezone info
    has_tz = pd.api.types.is_datetime64tz_dtype(filtered_df[date_column])

    # Convert string dates to datetime if needed
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)

    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)

    # Handle timezone-aware vs timezone-naive comparison
    if has_tz:
        # If data has timezone but inputs don't, make inputs timezone-aware
        if start_date.tzinfo is None:
            # Use UTC as that's likely what the API uses
            start_date = pd.Timestamp(start_date).tz_localize("UTC")
        if end_date.tzinfo is None:
            end_date = pd.Timestamp(end_date).tz_localize("UTC")
    else:
        # If data doesn't have timezone but inputs do, make data timezone-aware
        # or make inputs timezone-naive
        if start_date.tzinfo is not None:
            start_date = start_date.tz_localize(None)
        if end_date.tzinfo is not None:
            end_date = end_date.tz_localize(None)

    # Apply filtering
    filtered_df = filtered_df[(filtered_df[date_column] >= start_date) & (filtered_df[date_column] <= end_date)]

    return filtered_df


def group_by_interval(df, date_column, interval, agg_column=None, agg_func="count"):
    """Group DataFrame by specified time interval."""
    if interval is None:
        interval = "ME"  # Default to monthly (month end)

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Ensure the date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df_copy[date_column]):
        df_copy[date_column] = pd.to_datetime(df_copy[date_column])

    # Get min and max dates from the data
    min_date = df_copy[date_column].min() if not df_copy.empty else None
    max_date = df_copy[date_column].max() if not df_copy.empty else None

    # Get current date to ensure we include all dates up to current date
    current_date = pd.Timestamp.now()

    # If there's no data, use a default range
    if min_date is None or pd.isna(min_date):
        min_date = pd.Timestamp("2023-01-01")
        max_date = current_date
    else:
        # Make sure max_date includes the current date
        # Check if the dates have timezone info
        has_tz = pd.api.types.is_datetime64tz_dtype(df_copy[date_column])

        if has_tz:
            # If data has timezone, make current_date timezone-aware
            if current_date.tzinfo is None:
                current_date = current_date.tz_localize("UTC")
        else:
            # If data doesn't have timezone but current_date does, make current_date timezone-naive
            if current_date.tzinfo is not None:
                current_date = current_date.tz_localize(None)

        max_date = max(max_date, current_date)

    # Create a date range DataFrame with all intervals between min and max date
    try:
        date_range = pd.DataFrame({date_column: pd.date_range(start=min_date, end=max_date, freq=interval)})
    except Exception as e:
        # Handle case where the date range creation fails
        logger.error(f"Error creating date range: {e}. Using simple range instead.")
        # Create a simple range from min to max with monthly frequency
        simple_range = pd.date_range(start=min_date, end=max_date, freq="ME")
        date_range = pd.DataFrame({date_column: simple_range})

    # Group by the specified interval
    if agg_column is None:
        # Just count occurrences
        result = df_copy.groupby(pd.Grouper(key=date_column, freq=interval)).size().reset_index()
        result.columns = [date_column, "count"]
    else:
        # Apply the specified aggregation function
        result = df_copy.groupby(pd.Grouper(key=date_column, freq=interval)).agg({agg_column: agg_func}).reset_index()

    # Get the timezone info from the result
    result_has_tz = False
    if not result.empty and pd.api.types.is_datetime64tz_dtype(result[date_column]):
        result_has_tz = True

    # Ensure the date_range has the same timezone as the result
    if result_has_tz and not pd.api.types.is_datetime64tz_dtype(date_range[date_column]):
        date_range[date_column] = date_range[date_column].dt.tz_localize("UTC")
    elif not result_has_tz and pd.api.types.is_datetime64tz_dtype(date_range[date_column]):
        date_range[date_column] = date_range[date_column].dt.tz_localize(None)

    # Merge with the complete date range to ensure all dates are present
    # Use outer join and fill NaN with 0
    complete_result = pd.merge(date_range, result, on=date_column, how="left")

    # Fill missing count values with 0
    if agg_column is None:
        complete_result["count"] = complete_result["count"].fillna(0).astype(int)
    else:
        complete_result[agg_column] = complete_result[agg_column].fillna(0)

    # Remove time component from dates
    complete_result[date_column] = complete_result[date_column].dt.date

    return complete_result


def calculate_cumulative(df, date_column, count_column="count"):
    """Calculate cumulative sum of count column."""
    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Sort by date
    df_copy = df_copy.sort_values(by=date_column)

    # Calculate cumulative sum
    df_copy["cumulative"] = df_copy[count_column].cumsum()

    return df_copy


def create_line_chart(df, x_column, y_column, title, color=None, labels=None):
    """Create a line chart using Plotly Express."""
    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Check if the dataframe is empty
    if df_copy.empty:
        # Return an empty figure with a message
        fig = px.line(
            pd.DataFrame({x_column: [], y_column: []}), x=x_column, y=y_column, title=title + " (No data available)"
        )
        return fig

    # Ensure date formatting (handles both datetime objects and date strings)
    if pd.api.types.is_datetime64_any_dtype(df_copy[x_column]) or (
        len(df_copy) > 0 and isinstance(df_copy[x_column].iloc[0], datetime)
    ):
        df_copy[x_column] = pd.to_datetime(df_copy[x_column]).dt.date

    fig = px.line(df_copy, x=x_column, y=y_column, color=color, title=title, labels=labels or {})

    # Format x-axis to show date only (no time)
    fig.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")

    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        height=450,
    )
    
    return fig


def create_bar_chart(df, x_column, y_column, title, color=None, labels=None):
    """Create a bar chart using Plotly Express."""
    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Check if the dataframe is empty
    if df_copy.empty:
        # Return an empty figure with a message
        fig = px.bar(
            pd.DataFrame({x_column: [], y_column: []}), x=x_column, y=y_column, title=title + " (No data available)"
        )
        return fig

    # Ensure date formatting if x_column contains dates
    if pd.api.types.is_datetime64_any_dtype(df_copy[x_column]) or (
        len(df_copy) > 0 and isinstance(df_copy[x_column].iloc[0], datetime)
    ):
        df_copy[x_column] = pd.to_datetime(df_copy[x_column]).dt.date

    fig = px.bar(df_copy, x=x_column, y=y_column, color=color, title=title, labels=labels or {})

    # Format x-axis to show date only (no time) if x is a date column
    if pd.api.types.is_datetime64_any_dtype(df_copy[x_column]) or isinstance(df_copy[x_column].iloc[0], datetime):
        fig.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")

    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        height=450,
    )
    
    return fig


def create_auto_scrolling_image_gallery(images_data, title, height="180px"):
    """
    Create an auto-scrolling horizontal image gallery.
    """
    logger.info(f"Creating gallery for {title} with {len(images_data)} images")

    # Generate a unique ID based on the title
    id_base = title.lower().replace(" ", "-")
    gallery_id = f"{id_base}-gallery"
    refresh_id = f"{id_base}-refresh-button"

    if not images_data:
        return html.Div(
            [
                html.Div(
                    [
                        html.H5(title),
                        html.Button("Reshuffle", id=refresh_id, className="btn btn-sm btn-outline-primary ml-2"),
                    ],
                    className="d-flex justify-content-between align-items-center",
                ),
                html.P("No images available", className="text-muted"),
            ],
            className="mb-4",
        )

    # Limit to 50 images before duplication
    images_data = images_data[:50]
    logger.info(f"Limited to {len(images_data)} images before creating cards")

    # Create image cards with clickable links
    image_cards = []
    for img in images_data:
        if img.get("url"):
            # Ensure link is a full URL to the external data portal
            external_link = img.get("link", "#")

            # Create a card with a link
            image_cards.append(
                html.Div(
                    [
                        html.A(
                            [
                                html.Img(
                                    src=img["url"],
                                    style={
                                        "height": "120px",
                                        "objectFit": "cover",
                                        "borderRadius": "4px",
                                        "width": "100%",
                                    },
                                ),
                                html.Div(
                                    img.get("caption", ""),
                                    style={
                                        "fontSize": "12px",
                                        "overflow": "hidden",
                                        "textOverflow": "ellipsis",
                                        "whiteSpace": "nowrap",
                                        "maxWidth": "150px",
                                        "textAlign": "center",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            href=external_link,
                            target="_blank",  # Open in new tab
                            title=f"View {img.get('caption', 'item')} details in the Data Portal",
                            style={"textDecoration": "none", "color": "inherit"},
                            className="external-link",
                        )
                    ],
                    className="image-card",
                )
            )

    logger.info(f"Created {len(image_cards)} image cards")

    # Duplicate the cards to create a seamless scrolling effect
    all_cards = image_cards + image_cards
    logger.info(f"Total cards after duplication: {len(all_cards)}")

    # Create the gallery with CSS animations defined in assets/styles.css
    return html.Div(
        [
            html.Div(
                [
                    html.H5(title),
                    html.Button("Reshuffle", id=refresh_id, className="btn btn-sm btn-outline-primary ml-2"),
                ],
                className="d-flex justify-content-between align-items-center",
            ),
            html.Div(
                html.Div(all_cards, className="scrolling-content", id=gallery_id),
                className="gallery-container",
                style={"height": height},
            ),
        ],
        className="mb-4",
    )


def create_related_items_links(items, item_type):
    """Creates a list of links to related items in the data portal.

    This function generates a list of links for items that are related to a selected row
    in a data table. When a user clicks on a row in a data table, the corresponding
    related items will be displayed in a collapsible panel below the plot.

    The links include the item ID and title/name, and they open the item's page
    in the CryoET Data Portal in a new browser tab.

    Args:
        items (list): List of dicts containing item data with at least an 'id' field
        item_type (str): Type of item ('deposition', 'dataset', 'run', 'tomogram', or 'annotation')

    Returns:
        dash component: A component containing a list of links
    """
    if not items or len(items) == 0:
        return html.P("No items to display")

    # Base paths for each item type
    base_paths = {
        "deposition": "/depositions/",
        "dataset": "/datasets/",
        "run": "/runs/",
        "tomogram": "/tomograms/",
        "annotation": "/annotations/",
    }

    # Get the correct base path or default to depositions
    base_path = base_paths.get(item_type.lower(), "/depositions/")

    # Format human-readable names based on item_type and available fields
    def get_display_name(item):
        if item_type.lower() == "deposition":
            return f"Deposition ID: {item['id']} - {item.get('title', '')}"
        elif item_type.lower() == "dataset":
            return f"Dataset ID: {item['id']} - {item.get('title', '')}"
        elif item_type.lower() == "run":
            return f"Run ID: {item['id']} - {item.get('title', '')}"
        elif item_type.lower() == "tomogram":
            return f"Tomogram ID: {item['id']} - {item.get('name', '')}"
        elif item_type.lower() == "annotation":
            return f"Annotation ID: {item['id']} - {item.get('name', '')}"
        else:
            return f"Item ID: {item['id']}"

    # Create list of links
    links = [
        html.Li(
            html.A(
                get_display_name(item),
                href=f"https://cryoetdataportal.czscience.com{base_path}{item['id']}",
                target="_blank",
            ),
            className="mb-1",
        )
        for item in items
    ]

    return html.Ul(links, className="list-unstyled")


def create_related_items_grid_gallery(items, item_type, title="Related Items", max_items=36):
    """
    Create a grid gallery of related items with a reshuffle button.

    Args:
        items (list): List of dictionaries containing related items data
        item_type (str): Type of item ('run' or 'tomogram')
        title (str): Title to display above the gallery
        max_items (int): Maximum number of items to display (default: 36 for 6x6 grid)

    Returns:
        dash component: A grid gallery with related items and reshuffle button
    """
    if not items or len(items) == 0:
        return html.Div([html.H5(title), html.P("No related items found", className="text-muted")])

    # Use a consistent title for the same type of gallery to ensure the callbacks work
    normalized_title = title
    if "added in" in title.lower():
        normalized_title = f"{item_type.capitalize()}s added in period"
    elif "up to" in title.lower():
        normalized_title = f"{item_type.capitalize()}s up to date"
    elif "reconstruction method" in title.lower():
        normalized_title = f"{item_type.capitalize()}s with reconstruction method"
    elif "processing method" in title.lower():
        normalized_title = f"{item_type.capitalize()}s with processing method"
    elif "voxel spacing" in title.lower():
        normalized_title = f"{item_type.capitalize()}s with voxel spacing"
    elif "sample type" in title.lower():
        normalized_title = f"{item_type.capitalize()}s with sample type"
    elif "organism" in title.lower():
        normalized_title = f"{item_type.capitalize()}s with organism"

    # Generate a unique ID based on the normalized title
    id_base = f"related-{item_type}-{normalized_title.lower().replace(' ', '-')}"
    gallery_id = f"{id_base}-gallery"
    refresh_id = f"{id_base}-refresh-button"
    items_store_id = f"{id_base}-items-store"

    # Create a store component to hold all items
    store = dcc.Store(id=items_store_id, data=items)

    # Randomize and limit items
    selected_items = items.copy()
    random.shuffle(selected_items)
    selected_items = selected_items[:max_items]

    # Create image cards
    image_cards = []
    grid_size = 6  # 6x6 grid (or wider if container allows)

    for item in selected_items:
        item_id = item.get("id", "")
        if not item_id:
            continue

        # Get image URL from key_photo_url
        image_url = item.get("key_photo_url", "")
        if not image_url:
            continue

        # Create caption based on item type
        if item_type.lower() == "run":
            caption = f"Run {item_id}"
            if "title" in item and item["title"]:
                caption += f": {item['title'][:20]}"
            link = f"{PORTAL_BASE_URL}/runs/{item_id}"
        elif item_type.lower() == "tomogram":
            caption = f"Tomogram {item_id}"
            # Use run_id for tomogram links
            run_id = item.get("run_id", "")
            if run_id:
                link = f"{PORTAL_BASE_URL}/runs/{run_id}"
            else:
                link = f"{PORTAL_BASE_URL}/depositions/{item.get('deposition_id', '')}"
        else:
            caption = f"Item {item_id}"
            link = "#"

        # Create a card with image and caption
        image_cards.append(
            dbc.Col(
                html.Div(
                    [
                        html.A(
                            [
                                html.Img(
                                    src=image_url,
                                    style={
                                        "height": "150px",  # Increased height
                                        "objectFit": "cover",
                                        "borderRadius": "4px",
                                        "width": "100%",
                                    },
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
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            href=link,
                            target="_blank",
                            title=f"View {caption} details in the Data Portal",
                            style={"textDecoration": "none", "color": "inherit"},
                            className="external-link",
                        )
                    ],
                    className="related-image-card mb-3",
                )
            )
        )

    # Fill remaining slots with empty cards if needed
    while len(image_cards) < max_items:
        image_cards.append(dbc.Col())

    # Arrange cards in rows (grid_size cards per row)
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i : i + grid_size], className="mb-3"))

    # Create the gallery with header and reshuffle button
    return html.Div(
        [
            store,
            html.Div(
                [
                    html.H5(title),
                    html.Button("Reshuffle", id=refresh_id, className="btn btn-sm btn-outline-primary ml-2"),
                ],
                className="d-flex justify-content-between align-items-center mb-3",
            ),
            html.Div(rows, id=gallery_id, className="related-grid-gallery"),
        ],
        className="mt-4",
    )


def create_download_buttons(id_prefix, data_type):
    """Create download buttons for CSV data export and SVG chart export.
    
    Args:
        id_prefix (str): Prefix for component IDs
        data_type (str): Type of data being exported (e.g., 'depositions', 'datasets')
        
    Returns:
        dash component: Download buttons and hidden divs for storing data
    """
    return html.Div([
        # CSV Download Button
        html.Button(
            [html.I(className="fas fa-download mr-2"), " Download CSV"],
            id=f"{id_prefix}-download-button",
            className="btn btn-sm btn-outline-secondary ml-2",
            title="Download data as CSV",
        ),
        dcc.Download(id=f"{id_prefix}-download-csv"),
        
        # SVG Download Button
        html.Button(
            [html.I(className="fas fa-file-image mr-2"), " Download SVG"],
            id=f"{id_prefix}-download-svg-button",
            className="btn btn-sm btn-outline-secondary ml-2",
            title="Download chart as SVG",
        ),
        dcc.Download(id=f"{id_prefix}-download-svg"),
        
        # Hidden div to store the data for download
        html.Div(id=f"{id_prefix}-download-data", style={"display": "none"}),
    ], className="d-inline")


def generate_csv_download(df, data_type):
    """Generate a CSV download string from a dataframe.
    
    Args:
        df (pandas.DataFrame): The dataframe to convert to CSV
        data_type (str): Type of data being exported (used in filename)
        
    Returns:
        dict: Dictionary with the download data and filename
    """
    # Create CSV string from dataframe
    csv_string = df.to_csv(index=False, encoding='utf-8')
    
    # Create filename with data type and current date
    filename = f"{data_type}_{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    return dict(content=csv_string, filename=filename)


def generate_svg_download(fig, data_type):
    """Generate an SVG download from a plotly figure using Kaleido.
    
    Args:
        fig (plotly.graph_objects.Figure): The figure to convert to SVG
        data_type (str): Type of data being exported (used in filename)
        
    Returns:
        dict: Dictionary with the download data and filename
    """
    try:
        # Import plotly.io to use Kaleido
        import plotly.io as pio
        import base64
        
        # Create filename with data type and current date
        filename = f"{data_type}_{datetime.now().strftime('%Y-%m-%d')}.svg"
        
        # Convert figure to SVG bytes using Kaleido
        svg_bytes = pio.to_image(fig, format="svg", width=800, height=450, scale=2, engine="kaleido")
        
        # Encode bytes as base64 for Dash download component
        encoded = base64.b64encode(svg_bytes).decode('utf-8')
        
        # Return the image content for the download component with base64 encoding
        return dict(content=encoded, filename=filename, type="image/svg+xml", base64=True)
    except Exception as e:
        # Log the error
        import logging
        logging_error = logging.getLogger(__name__)
        logging_error.error(f"Error generating SVG download: {e}")
        import traceback
        logging_error.error(traceback.format_exc())
        
        # Return a simple SVG with an error message
        error_svg = f'''
        <svg width="800" height="450" xmlns="http://www.w3.org/2000/svg">
            <rect width="800" height="450" fill="#f8f9fa" />
            <text x="50" y="50" font-family="Arial" font-size="20" fill="red">
                Error generating SVG: {str(e)}
            </text>
            <text x="50" y="80" font-family="Arial" font-size="16">
                Please try again or contact support if the problem persists.
            </text>
        </svg>
        '''.encode('utf-8')
        
        # Encode error SVG as base64
        encoded_error = base64.b64encode(error_svg).decode('utf-8')
        
        filename = f"error_{data_type}_{datetime.now().strftime('%Y-%m-%d')}.svg"
        return dict(content=encoded_error, filename=filename, type="image/svg+xml", base64=True)
