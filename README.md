# CryoET Data Portal Dashboard

A web dashboard built with Dash Plotly that provides visualizations and statistics about the cryoET data portal.

## Features

- Interactive dashboard with multiple pages for different categories:
  - Depositions
  - Datasets
  - Runs
  - Tomograms
  - Annotations

- Each page displays various statistics with:
  - Interactive tables showing raw data
  - Line charts and bar charts for visualizing trends
  - Date range and interval controls for time-based data

- Key visualizations include:
  - Number of items added per month
  - Cumulative growth over time
  - Distribution by sample type, organism, methods, etc.

## Installation

1. Clone this repository:
```
git clone https://github.com/your-username/cryoet-data-portal-dashboard.git
cd cryoet-data-portal-dashboard
```

2. Create a virtual environment (recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package and dependencies:
```
pip install -e .
```

## Usage

### Running the Dashboard

To launch the dashboard, run:

```
python -m cryoet_data_portal_dashboard.app
```

The dashboard will be available at http://127.0.0.1:8050/ in your web browser.

### Navigation

- Use the sidebar to navigate between different categories
- Each page contains multiple cards with tables and visualizations
- Time-based visualizations include controls to adjust the date range and interval
- Tables display the raw data that's shown in the visualizations

## Technical Details

- Built with Dash Plotly for interactive web visualizations
- Uses the cryoET data portal Python API client to retrieve data
- Data processing handled with pandas
- Responsive design with Dash Bootstrap Components

## Requirements

- Python 3.10 or higher
- Dash
- Plotly
- Pandas
- Dash Bootstrap Components
- cryoet-data-portal (v4.3.1 or higher)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 