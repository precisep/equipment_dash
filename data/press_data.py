import pandas as pd
import sqlite3
from io import BytesIO
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime



def convert_micro_to_datetime(ts):
    """Convert timestamp from microseconds to a human-readable datetime format."""
    return datetime.utcfromtimestamp(ts / 1e6).strftime('%Y-%m-%d %H:%M:%S')

def convert_to_pressure(raw_value):
    """Convert raw pressure values to human-readable format."""
    scaling_factor = 1e6
    return raw_value / scaling_factor if pd.notnull(raw_value) else 0.0

def fetch_all_data_from_uploaded_file(contents):
    """Fetch and process data from the uploaded SQLite file."""
    content_type, content_string = contents.split(',')

    
    decoded = base64.b64decode(content_string)

    
    buffer = BytesIO(decoded)

    
    with sqlite3.connect(f"file::memory:?cache=shared", uri=True) as conn:
        conn = sqlite3.connect(buffer)
        query = """
        SELECT TS, Val1, Val2, Val3
        FROM TblTrendData
        """
        df = pd.read_sql_query(query, conn)

    # Convert timestamp and values
    df['Timestamp'] = df['TS'].apply(convert_micro_to_datetime)
    df['Extrusion Time'] = df['Val1'].apply(convert_to_pressure)
    df['Dead Cycle Time'] = df['Val2'].apply(convert_to_pressure)
    df['Full Cycle Time'] = df['Val3'].apply(convert_to_pressure)

    return df

def create_plot(df):
    """Create a Plotly figure with subplots based on the processed data."""
    # Create subplots for the three different values
    fig = make_subplots(
        rows=3, cols=1,  # Three subplots in one column
        shared_xaxes=True,  # Share the x-axis (Timestamp) across plots
        vertical_spacing=0.1,  # Space between plots
        subplot_titles=("Extrusion Time", "Dead Cycle Time", "Full Cycle Time")
    )

    # Add Extrusion Time to the first subplot
    fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Extrusion Time'], mode='lines', name='Extrusion Time'),
                  row=1, col=1)

    # Add Dead Cycle Time to the second subplot
    fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Dead Cycle Time'], mode='lines', name='Dead Cycle Time'),
                  row=2, col=1)

    # Add Full Cycle Time to the third subplot
    fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Full Cycle Time'], mode='lines', name='Full Cycle Time'),
                  row=3, col=1)

   s
    fig.update_layout(
        height=800,  # Adjust the height of the figure
        title_text="Trend Data Over Time",  # Overall title
        xaxis_title="Timestamp",  # Shared X-axis title
        showlegend=False  # Hide the legend to avoid redundancy
    )

    return fig
