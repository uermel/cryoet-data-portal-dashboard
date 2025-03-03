"""Runs page for the dashboard."""
import pandas as pd
import dash
from dash import dcc, html, callback, Output, Input, dash_table, State
import dash_bootstrap_components as dbc
import plotly.express as px
from datetime import datetime
import logging
import random

from cryoet_data_portal_dashboard.components import (
    create_card, 
    create_date_range_selector, 
    filter_by_date_range,
    group_by_interval,
    calculate_cumulative,
    create_line_chart,
    create_bar_chart,
    create_auto_scrolling_image_gallery,
    create_related_items_grid_gallery
)
from cryoet_data_portal_dashboard.data_utils import (
    fetch_runs_with_dataset_dates,
    get_runs_by_sample_type,
    get_runs_by_organism,
    get_runs_with_annotations,
    get_run_images,
    fetch_tomograms,
    PORTAL_BASE_URL
)
from cryoet_data_portal_dashboard.cache import cache

# Get a logger for this module
logger = logging.getLogger(__name__)

# Get run images for the gallery
run_images = get_run_images()
print(len(run_images))

# Define the layout for the runs page
layout = dbc.Container(
    [
        dcc.Location(id="runs-url", refresh=False),  # Add location component to provide input for callbacks
        html.H2("Runs", className="mb-3"),  # Changed from H1 to H2 and removed "Dashboard"
        
        # Image Gallery
        create_auto_scrolling_image_gallery(
            run_images, 
            "Example Runs"
        ),
        
        # Interactive Table Info Alert
        dbc.Alert(
            [
                html.H5("Interactive Table Instructions", className="alert-heading"),
                html.P(
                    "The tables below are interactive. Click on any row to highlight it and view related runs "
                    "data. A gallery of related run images will appear below the chart. You can filter data using "
                    "the date range selectors. For sample type and organism tables, clicking on a row will show runs "
                    "of that specific type."
                ),
            ],
            color="info",
            className="mb-4",
        ),
        
        # Card 1: Number of runs added per month
        create_card(
            title="Number of Runs Added Per Month",
            table_component=html.Div(
                [
                    create_date_range_selector("runs-added"),
                    html.Div(id="runs-added-table"),
                ]
            ),
            plot_component=dcc.Graph(id="runs-added-plot"),
            id_prefix="runs-added"
        ),
        
        # Card 2: Cumulative number of runs per month
        create_card(
            title="Cumulative Number of Runs",
            table_component=html.Div(
                [
                    create_date_range_selector("runs-cumulative"),
                    html.Div(id="runs-cumulative-table"),
                ]
            ),
            plot_component=dcc.Graph(id="runs-cumulative-plot"),
            id_prefix="runs-cumulative"
        ),
        
        # Card 3: Runs per sample type
        create_card(
            title="Runs by Sample Type",
            table_component=html.Div(id="runs-sample-type-table"),
            plot_component=dcc.Graph(id="runs-sample-type-plot"),
            id_prefix="runs-sample-type"
        ),
        
        # Card 4: Runs per organism name
        create_card(
            title="Runs by Organism",
            table_component=html.Div(id="runs-organism-table"),
            plot_component=dcc.Graph(id="runs-organism-plot"),
            id_prefix="runs-organism"
        ),
        
        # Card 5: Runs with annotations
        create_card(
            title="Runs with Annotations",
            table_component=html.Div(id="runs-with-annotations-table"),
            plot_component=dcc.Graph(id="runs-with-annotations-plot"),
            id_prefix="runs-with-annotations"
        ),
    ],
    fluid=True,
    className="py-3",
)


# Callback for runs added per month
@callback(
    [Output("runs-added-table", "children"),
     Output("runs-added-plot", "figure")],
    [Input("runs-added-date-range", "start_date"),
     Input("runs-added-date-range", "end_date"),
     Input("runs-added-interval", "value"),
     Input("runs-added-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_runs_added(start_date, end_date, interval, n_clicks):
    # Fetch data
    df = fetch_runs_with_dataset_dates()
    
    # Use deposition_date as the date column
    date_col = 'deposition_date'
    
    # Filter by date range
    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)
    
    # Group by interval
    grouped_df = group_by_interval(filtered_df, date_col, interval)
    
    # Create the table
    table = dash_table.DataTable(
        id='runs-added-datatable',
        data=grouped_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Runs Added", "id": "count"}
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
        "Runs Added Over Time",
        labels={"count": "Number of Runs", date_col: "Date"}
    )
    
    return table, fig


# Callback for cumulative runs
@callback(
    [Output("runs-cumulative-table", "children"),
     Output("runs-cumulative-plot", "figure")],
    [Input("runs-cumulative-date-range", "start_date"),
     Input("runs-cumulative-date-range", "end_date"),
     Input("runs-cumulative-interval", "value"),
     Input("runs-cumulative-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_runs_cumulative(start_date, end_date, interval, n_clicks):
    # Fetch data
    df = fetch_runs_with_dataset_dates()
    
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
        id='runs-cumulative-datatable',
        data=cumulative_df.to_dict('records'),
        columns=[
            {"name": "Date", "id": date_col, "type": "datetime", "format": {"specifier": "%Y-%m-%d"}},
            {"name": "Cumulative Runs", "id": "cumulative"}
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
        "Cumulative Runs Over Time",
        labels={"cumulative": "Cumulative Number of Runs", date_col: "Date"}
    )
    
    return table, fig


# Callback for runs by sample type
@callback(
    [Output("runs-sample-type-table", "children"),
     Output("runs-sample-type-plot", "figure")],
    [Input("runs-url", "pathname"),
     Input("runs-sample-type-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_runs_by_sample_type(pathname, n_clicks):
    # Get data
    df = get_runs_by_sample_type()
    
    # Create the table
    table = dash_table.DataTable(
        id='runs-sample-type-datatable',
        data=df.to_dict('records'),
        columns=[
            {"name": "Sample Type", "id": "sample_type"},
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
        'sample_type', 
        'count', 
        "Runs by Sample Type",
        labels={"count": "Number of Runs", "sample_type": "Sample Type"}
    )
    
    return table, fig


# Callback for runs by organism
@callback(
    [Output("runs-organism-table", "children"),
     Output("runs-organism-plot", "figure")],
    [Input("runs-url", "pathname"),
     Input("runs-organism-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_runs_by_organism(pathname, n_clicks):
    # Get data
    df = get_runs_by_organism()
    
    # Create the table
    table = dash_table.DataTable(
        id='runs-organism-datatable',
        data=df.to_dict('records'),
        columns=[
            {"name": "Organism", "id": "organism_name"},
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
        'organism_name', 
        'count', 
        "Runs by Organism",
        labels={"count": "Number of Runs", "organism_name": "Organism"}
    )
    
    return table, fig


# Callback for runs with annotations
@callback(
    [Output("runs-with-annotations-table", "children"),
     Output("runs-with-annotations-plot", "figure")],
    [Input("runs-url", "pathname"),
     Input("runs-with-annotations-refresh-button", "n_clicks")]
)
@cache.memoize(timeout=300)  # Cache for 5 minutes
def update_runs_with_annotations(pathname, n_clicks):
    # Get data
    df = get_runs_with_annotations()
    
    if not df.empty and 'has_annotations' in df.columns:
        # Calculate the summary counts
        total_runs = len(df)
        runs_with_annotations = df['has_annotations'].sum()
        runs_without_annotations = total_runs - runs_with_annotations
        
        # Create summary data for the table
        summary_data = [{
            "measure": "Total Runs",
            "value": total_runs
        }, {
            "measure": "Runs with Annotations",
            "value": runs_with_annotations
        }, {
            "measure": "Runs without Annotations", 
            "value": runs_without_annotations
        }]
        
        # Create the table with proper styling
        table = dash_table.DataTable(
            id='runs-with-annotations-datatable',
            data=summary_data,
            columns=[
                {"name": "Measure", "id": "measure"},
                {"name": "Count", "id": "value"}
            ],
            style_table={'overflowX': 'auto', 'width': '100%'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
            style_data={'backgroundColor': 'white'},
            # Add interactive styling
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
        
        # Create data for the stacked bar chart
        bar_data = pd.DataFrame([
            {"category": "Runs", "status": "With Annotations", "count": runs_with_annotations},
            {"category": "Runs", "status": "Without Annotations", "count": runs_without_annotations}
        ])
        
        # Create the stacked bar chart
        fig = px.bar(
            bar_data,
            x="category",
            y="count",
            color="status",
            title="Runs With and Without Annotations",
            labels={"count": "Number of Runs", "status": "Annotation Status"},
            color_discrete_map={
                "With Annotations": "#636EFA",  # Plotly blue
                "Without Annotations": "#EF553B"  # Plotly red
            }
        )
        
        # Add text labels showing the counts
        fig.update_traces(textposition='inside', texttemplate='%{y}')
        
        # Update layout for better appearance
        fig.update_layout(
            barmode='stack',
            xaxis_title=None,  # Remove x-axis title
            xaxis=dict(tickangle=0),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    else:
        # Create empty table and plot if no data
        table = dash_table.DataTable(
            data=[],
            columns=[
                {"name": "Measure", "id": "measure"},
                {"name": "Count", "id": "value"}
            ],
            style_table={'overflowX': 'auto', 'width': '100%'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
        )
        
        fig = px.bar(
            pd.DataFrame({"category": [], "status": [], "count": []}),
            x="category",
            y="count",
            color="status",
            title="Runs With and Without Annotations"
        )
        fig.update_layout(barmode='stack')
    
    return table, fig


@callback(
    Output("example-runs-gallery", "children"),
    Input("example-runs-refresh-button", "n_clicks")
)
def refresh_run_images(n_clicks):
    """
    Refresh the run images gallery when the reshuffle button is clicked.
    """
    if n_clicks is None:
        return dash.no_update
    
    # Get fresh random images, using n_clicks as a cache buster
    images = get_run_images(cache_buster=n_clicks)
    logger.info(f"Got {len(images)} images from get_run_images(), cache_buster={n_clicks}")
    
    # Limit to 50 images before duplication
    images = images[:50]
    logger.info(f"Limited to {len(images)} images before creating cards")
    
    # Create image cards with clickable links
    image_cards = []
    for img in images:
        if img.get('url'):
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
                    href=img.get('link'),
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

# Callback to show a grid gallery of related runs for the runs-added table
@callback(
    [Output("runs-added-related-items", "children"),
     Output("runs-added-related-items-collapse", "is_open")],
    [Input("runs-added-datatable", "active_cell"),
     Input("runs-added-datatable", "data")]
)
def display_runs_added_related_items(active_cell, data):
    """
    Display a grid gallery of runs added during the selected time period.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related runs"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        selected_date = selected_row['deposition_date']
        
        logger.info(f"Runs Added - Selected date: {selected_date}")
        
        # Fetch all runs
        all_runs = fetch_runs_with_dataset_dates()
        
        if all_runs.empty:
            return html.P("No runs data available"), True
        
        # Convert the selected date string to a date object (removing time and timezone)
        if isinstance(selected_date, str):
            selected_date = pd.to_datetime(selected_date).date()
        else:
            selected_date = pd.to_datetime(selected_date).date()
        
        # Extract year and month from selected date for filtering
        selected_year = selected_date.year
        selected_month = selected_date.month
        
        # Convert run dates to date objects and extract year and month
        all_runs['deposition_date'] = pd.to_datetime(all_runs['deposition_date'])
        all_runs['year'] = all_runs['deposition_date'].dt.year
        all_runs['month'] = all_runs['deposition_date'].dt.month
        
        # Filter runs from that month
        related_runs = all_runs[
            (all_runs['year'] == selected_year) & 
            (all_runs['month'] == selected_month)
        ]
        
        selected_year_month = f"{selected_year}-{selected_month:02d}"
        logger.info(f"Runs Added - Found {len(related_runs)} related runs for {selected_year_month}")
        
        # Now get tomogram images to add to runs
        tomograms_df = fetch_tomograms()
        if not tomograms_df.empty and 'key_photo_url' in tomograms_df.columns and 'run_id' in tomograms_df.columns:
            # Filter tomograms to those with images
            tomograms_df = tomograms_df[tomograms_df['key_photo_url'].notna()]
            
            # Get the first tomogram for each run (to get its image)
            first_tomograms = tomograms_df.sort_values('id').groupby('run_id').first().reset_index()
            first_tomograms = first_tomograms[['run_id', 'key_photo_url']]
            
            # Merge run data with tomogram images
            related_runs = related_runs.merge(
                first_tomograms,
                left_on='id',
                right_on='run_id',
                how='left'
            )
            
            logger.info(f"Runs Added - Merged {len(related_runs)} runs with tomogram images")
        else:
            logger.warning("Runs Added - No tomogram images available to merge with runs")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_runs.to_dict('records')
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            return html.P(f"No runs found for {selected_year_month}"), True
            
        # If too many items, randomly sample
        if len(related_items) > 100:
            related_items = random.sample(related_items, 100)
        
        # Create the grid gallery of related runs
        gallery = create_related_items_grid_gallery(related_items, 'run', f"Runs added in {selected_year_month}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.error(f"Error in display_runs_added_related_items: {e}")
        return html.P(f"An error occurred: {str(e)}"), True

# Callback to show a grid gallery of related runs for the runs-cumulative table
@callback(
    [Output("runs-cumulative-related-items", "children"),
     Output("runs-cumulative-related-items-collapse", "is_open")],
    [Input("runs-cumulative-datatable", "active_cell"),
     Input("runs-cumulative-datatable", "data")]
)
def display_runs_cumulative_related_items(active_cell, data):
    """
    Display a grid gallery of runs up to the selected time period.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related runs"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        selected_date = selected_row['deposition_date']
        
        logger.info(f"Runs Cumulative - Selected date: {selected_date}")
        
        # Fetch all runs
        all_runs = fetch_runs_with_dataset_dates()
        
        if all_runs.empty:
            return html.P("No runs data available"), True
        
        # Convert the selected date string to a datetime object for comparison
        # Convert to string first to ensure it's timezone-naive
        if isinstance(selected_date, str):
            selected_date = pd.to_datetime(selected_date).date()
        else:
            selected_date = pd.to_datetime(selected_date).date()
        
        # Convert all deposition_dates to date objects (removes time component and timezone)
        all_runs['date_only'] = pd.to_datetime(all_runs['deposition_date']).dt.date
        
        # Filter runs up to and including that date
        related_runs = all_runs[all_runs['date_only'] <= selected_date]
        
        logger.info(f"Runs Cumulative - Found {len(related_runs)} related runs up to {selected_date}")
        
        # Now get tomogram images to add to runs
        tomograms_df = fetch_tomograms()
        if not tomograms_df.empty and 'key_photo_url' in tomograms_df.columns and 'run_id' in tomograms_df.columns:
            # Filter tomograms to those with images
            tomograms_df = tomograms_df[tomograms_df['key_photo_url'].notna()]
            
            # Get the first tomogram for each run (to get its image)
            first_tomograms = tomograms_df.sort_values('id').groupby('run_id').first().reset_index()
            first_tomograms = first_tomograms[['run_id', 'key_photo_url']]
            
            # Merge run data with tomogram images
            related_runs = related_runs.merge(
                first_tomograms,
                left_on='id',
                right_on='run_id',
                how='left'
            )
            
            logger.info(f"Runs Cumulative - Merged {len(related_runs)} runs with tomogram images")
        else:
            logger.warning("Runs Cumulative - No tomogram images available to merge with runs")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_runs.to_dict('records')
        
        # If too many items, randomly sample
        if len(related_items) > 100:
            related_items = random.sample(related_items, 100)
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            return html.P(f"No runs found up to {selected_date}"), True
        
        # Create the grid gallery of related runs
        gallery = create_related_items_grid_gallery(related_items, 'run', f"Runs up to {selected_date}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.error(f"Error in display_runs_cumulative_related_items: {e}")
        return html.P(f"An error occurred: {str(e)}"), True

# Callback to show a grid gallery of related runs for the runs-sample-type table
@callback(
    [Output("runs-sample-type-related-items", "children"),
     Output("runs-sample-type-related-items-collapse", "is_open")],
    [Input("runs-sample-type-datatable", "active_cell"),
     Input("runs-sample-type-datatable", "data")]
)
def display_runs_sample_type_related_items(active_cell, data):
    """
    Display a grid gallery of runs for the selected sample type.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related runs"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        sample_type = selected_row.get('sample_type', '')
        
        logger.info(f"Runs Sample Type - Selected type: {sample_type}")
        
        if not sample_type:
            return html.P("No sample type selected"), True
        
        # Fetch all runs
        all_runs = fetch_runs_with_dataset_dates()
        
        if all_runs.empty or 'sample_type' not in all_runs.columns:
            return html.P("No run data available with sample type information"), True
        
        # Filter runs for the selected sample type
        related_runs = all_runs[all_runs['sample_type'] == sample_type]
        
        logger.info(f"Runs Sample Type - Found {len(related_runs)} related runs for {sample_type}")
        
        # Now get tomogram images to add to runs
        tomograms_df = fetch_tomograms()
        if not tomograms_df.empty and 'key_photo_url' in tomograms_df.columns and 'run_id' in tomograms_df.columns:
            # Filter tomograms to those with images
            tomograms_df = tomograms_df[tomograms_df['key_photo_url'].notna()]
            
            # Get the first tomogram for each run (to get its image)
            first_tomograms = tomograms_df.sort_values('id').groupby('run_id').first().reset_index()
            first_tomograms = first_tomograms[['run_id', 'key_photo_url']]
            
            # Merge run data with tomogram images
            related_runs = related_runs.merge(
                first_tomograms,
                left_on='id',
                right_on='run_id',
                how='left'
            )
            
            logger.info(f"Runs Sample Type - Merged {len(related_runs)} runs with tomogram images")
        else:
            logger.warning("Runs Sample Type - No tomogram images available to merge with runs")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_runs.to_dict('records')
        
        # If too many items, randomly sample
        if len(related_items) > 100:
            related_items = random.sample(related_items, 100)
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            return html.P(f"No runs found for sample type: {sample_type}"), True
        
        # Create the grid gallery of related runs
        gallery = create_related_items_grid_gallery(related_items, 'run', f"Runs with sample type: {sample_type}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.error(f"Error in display_runs_sample_type_related_items: {e}")
        return html.P(f"An error occurred: {str(e)}"), True

# Callback to show a grid gallery of related runs for the runs-organism table
@callback(
    [Output("runs-organism-related-items", "children"),
     Output("runs-organism-related-items-collapse", "is_open")],
    [Input("runs-organism-datatable", "active_cell"),
     Input("runs-organism-datatable", "data")]
)
def display_runs_organism_related_items(active_cell, data):
    """
    Display a grid gallery of runs for the selected organism.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related runs"), False
    
    try:
        # Get the row index from the active cell
        row_idx = active_cell['row']
        
        # Get the selected row data
        selected_row = data[row_idx]
        organism = selected_row.get('organism_name', '')
        
        logger.info(f"Runs Organism - Selected organism: {organism}")
        
        if not organism:
            return html.P("No organism selected"), True
        
        # Fetch all runs
        all_runs = fetch_runs_with_dataset_dates()
        
        if all_runs.empty or 'organism_name' not in all_runs.columns:
            return html.P("No run data available with organism information"), True
        
        # Filter runs for the selected organism
        related_runs = all_runs[all_runs['organism_name'] == organism]
        
        logger.info(f"Runs Organism - Found {len(related_runs)} related runs for {organism}")
        
        # Now get tomogram images to add to runs
        tomograms_df = fetch_tomograms()
        if not tomograms_df.empty and 'key_photo_url' in tomograms_df.columns and 'run_id' in tomograms_df.columns:
            # Filter tomograms to those with images
            tomograms_df = tomograms_df[tomograms_df['key_photo_url'].notna()]
            
            # Get the first tomogram for each run (to get its image)
            first_tomograms = tomograms_df.sort_values('id').groupby('run_id').first().reset_index()
            first_tomograms = first_tomograms[['run_id', 'key_photo_url']]
            
            # Merge run data with tomogram images
            related_runs = related_runs.merge(
                first_tomograms,
                left_on='id',
                right_on='run_id',
                how='left'
            )
            
            logger.info(f"Runs Organism - Merged {len(related_runs)} runs with tomogram images")
        else:
            logger.warning("Runs Organism - No tomogram images available to merge with runs")
        
        # Convert to list of dicts for the gallery creation function
        related_items = related_runs.to_dict('records')
        
        # If too many items, randomly sample
        if len(related_items) > 100:
            related_items = random.sample(related_items, 100)
        
        # If no items, provide a message
        if not related_items or len(related_items) == 0:
            return html.P(f"No runs found for organism: {organism}"), True
        
        # Create the grid gallery of related runs
        gallery = create_related_items_grid_gallery(related_items, 'run', f"Runs with organism: {organism}")
        
        # Return the gallery and set is_open to True
        return gallery, True
    
    except Exception as e:
        logger.error(f"Error in display_runs_organism_related_items: {e}")
        return html.P(f"An error occurred: {str(e)}"), True

# Callback to handle reshuffling of grid galleries
@callback(
    Output("related-run-runs-added-in-period-gallery", "children"),
    Input("related-run-runs-added-in-period-refresh-button", "n_clicks"),
    State("related-run-runs-added-in-period-items-store", "data")
)
def reshuffle_runs_added_gallery(n_clicks, stored_items):
    """Reshuffle the runs added in period gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling runs added gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
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
        caption = f"Run {item_id}"
        if 'title' in item and item['title']:
            caption += f": {item['title'][:20]}"
        link = f"{PORTAL_BASE_URL}/runs/{item_id}"
            
        # Create a card with image and caption
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
    
    # Fill remaining slots with empty cards if needed
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows (6 cards per row for 6x6 grid)
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

@callback(
    Output("related-run-runs-up-to-date-gallery", "children"),
    Input("related-run-runs-up-to-date-refresh-button", "n_clicks"),
    State("related-run-runs-up-to-date-items-store", "data")
)
def reshuffle_runs_cumulative_gallery(n_clicks, stored_items):
    """Reshuffle the runs up to date gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling runs cumulative gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
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
        caption = f"Run {item_id}"
        if 'title' in item and item['title']:
            caption += f": {item['title'][:20]}"
        link = f"{PORTAL_BASE_URL}/runs/{item_id}"
            
        # Create a card with image and caption
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
    
    # Fill remaining slots with empty cards if needed
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows (6 cards per row for 6x6 grid)
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

@callback(
    Output("related-run-runs-with-sample-type-gallery", "children"),
    Input("related-run-runs-with-sample-type-refresh-button", "n_clicks"),
    State("related-run-runs-with-sample-type-items-store", "data")
)
def reshuffle_runs_sample_type_gallery(n_clicks, stored_items):
    """Reshuffle the runs with sample type gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling runs sample type gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
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
        caption = f"Run {item_id}"
        if 'title' in item and item['title']:
            caption += f": {item['title'][:20]}"
        link = f"{PORTAL_BASE_URL}/runs/{item_id}"
            
        # Create a card with image and caption
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
    
    # Fill remaining slots with empty cards if needed
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows (6 cards per row for 6x6 grid)
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

@callback(
    Output("related-run-runs-with-organism-gallery", "children"),
    Input("related-run-runs-with-organism-refresh-button", "n_clicks"),
    State("related-run-runs-with-organism-items-store", "data")
)
def reshuffle_runs_organism_gallery(n_clicks, stored_items):
    """Reshuffle the runs for organism gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling runs organism gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
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
        caption = f"Run {item_id}"
        if 'title' in item and item['title']:
            caption += f": {item['title'][:20]}"
        link = f"{PORTAL_BASE_URL}/runs/{item_id}"
            
        # Create a card with image and caption
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
    
    # Fill remaining slots with empty cards if needed
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows (6 cards per row for 6x6 grid)
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

@callback(
    Output("related-run-runs-with-annotations-gallery", "children"),
    Input("related-run-runs-with-annotations-refresh-button", "n_clicks"),
    State("related-run-runs-with-annotations-items-store", "data")
)
def reshuffle_runs_with_annotations_gallery(n_clicks, stored_items):
    """Reshuffle the runs with annotations gallery."""
    if not n_clicks or not stored_items:
        return dash.no_update
    
    logger.info(f"Reshuffling runs with annotations gallery, n_clicks={n_clicks}, items={len(stored_items)}")
    
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
        caption = f"Run {item_id}"
        if 'title' in item and item['title']:
            caption += f": {item['title'][:20]}"
        link = f"{PORTAL_BASE_URL}/runs/{item_id}"
            
        # Create a card with image and caption
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
    
    # Fill remaining slots with empty cards if needed
    while len(image_cards) < 36:
        image_cards.append(dbc.Col())
    
    # Arrange cards in rows (6 cards per row for 6x6 grid)
    rows = []
    for i in range(0, len(image_cards), grid_size):
        rows.append(dbc.Row(image_cards[i:i+grid_size], className="mb-3"))
    
    return html.Div(rows, className="related-grid-gallery")

# Callback to show a grid gallery of related runs for the runs-with-annotations table
@callback(
    [Output("runs-with-annotations-related-items", "children"),
     Output("runs-with-annotations-related-items-collapse", "is_open")],
    [Input("runs-with-annotations-datatable", "active_cell"),
     Input("runs-with-annotations-datatable", "data")]
)
def display_runs_with_annotations_related_items(active_cell, data):
    """
    Display a grid gallery of runs based on annotation status.
    """
    # If no cell is clicked, hide the collapse
    if not active_cell or not data:
        return html.P("Click on a table cell to see related runs"), False
    
    # Get the row index from the active cell
    row_idx = active_cell['row']
    
    # Get the selected row data
    selected_row = data[row_idx]
    measure = selected_row.get('measure', '')
    
    logger.info(f"Runs With Annotations - Selected measure: {measure}")
    
    # Fetch all runs with annotation info
    all_runs = get_runs_with_annotations()
    
    if all_runs.empty:
        return html.P("No runs data available"), True
    
    # Filter runs based on the selected measure
    if measure == "Runs with Annotations":
        related_runs = all_runs[all_runs['has_annotations'] == True]
    elif measure == "Runs without Annotations":
        related_runs = all_runs[all_runs['has_annotations'] == False]
    else:  # Total Runs
        related_runs = all_runs
    
    logger.info(f"Runs With Annotations - Found {len(related_runs)} related runs for measure: {measure}")
    
    # Now get tomogram images to add to runs
    tomograms_df = fetch_tomograms()
    if not tomograms_df.empty and 'key_photo_url' in tomograms_df.columns and 'run_id' in tomograms_df.columns:
        # Filter tomograms to those with images
        tomograms_df = tomograms_df[tomograms_df['key_photo_url'].notna()]
        
        # Get the first tomogram for each run (to get its image)
        first_tomograms = tomograms_df.sort_values('id').groupby('run_id').first().reset_index()
        first_tomograms = first_tomograms[['run_id', 'key_photo_url']]
        
        # Merge run data with tomogram images
        related_runs = related_runs.merge(
            first_tomograms,
            left_on='id',
            right_on='run_id',
            how='left'
        )
        
        logger.info(f"Runs With Annotations - Merged {len(related_runs)} runs with tomogram images")
    else:
        logger.warning("Runs With Annotations - No tomogram images available to merge with runs")
    
    # Convert to list of dicts for the gallery creation function
    related_items = related_runs.to_dict('records')
    
    # If too many items, randomly sample
    if len(related_items) > 100:
        related_items = random.sample(related_items, 100)
    
    # If no items, provide a message
    if not related_items or len(related_items) == 0:
        return html.P(f"No runs found for {measure}"), True
    
    # Create the grid gallery of related runs
    gallery = create_related_items_grid_gallery(related_items, 'run', f"{measure}")
    
    # Return the gallery and set is_open to True
    return gallery, True 