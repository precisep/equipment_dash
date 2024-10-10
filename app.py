import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from dotenv import load_dotenv
import plotly.io as pio
from data.figure_creator import create_figure

pio.templates.default = "plotly_dark"

app = dash.Dash(
    __name__
)
server = app.server
load_dotenv()
API_KEY = os.getenv('GOOGLE_API_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_ALARM_SUMMARY = 'Alarm Summary'
RANGE_DATA_SOURCE = 'Data Source'
service = build('sheets', 'v4', developerKey=API_KEY)

try:
    result_alarm_summary = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_ALARM_SUMMARY).execute()
    rows_alarm_summary = result_alarm_summary.get('values', [])

    result_data_source = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_DATA_SOURCE).execute()
    rows_data_source = result_data_source.get('values', [])

    if rows_alarm_summary:
        headers_alarm = rows_alarm_summary[0]
        data_alarm_rows = rows_alarm_summary[1:]
        adjusted_data_alarm_rows = [row[:len(headers_alarm)] for row in data_alarm_rows]
        df_alarm_summary = pd.DataFrame(adjusted_data_alarm_rows, columns=headers_alarm)
    else:
        df_alarm_summary = pd.DataFrame()

    if rows_data_source:
        headers_data = rows_data_source[0]
        data_source_rows = rows_data_source[1:]
        df_data_source = pd.DataFrame(data_source_rows, columns=headers_data)
    else:
        df_data_source = pd.DataFrame()

except Exception as e:
    print(f"An error occurred: {e}")

df = df_data_source[['TSLast', 'TSActive', 'Unit Alarm Occurance']].copy()
df['TSLast'] = pd.to_datetime(df['TSLast'], errors='coerce')
df['TSActive'] = pd.to_datetime(df['TSActive'], errors='coerce')
invalid_rows = df[df['TSLast'].isna() | df['TSActive'].isna()]
if not invalid_rows.empty:
    print("Invalid datetime rows found:", invalid_rows)
df['Time_Difference_minutes'] = (df['TSLast'] - df['TSActive']).dt.total_seconds() / 60
df['Alarm'] = df['Unit Alarm Occurance']
df = df[['TSLast', 'TSActive', 'Alarm', 'Time_Difference_minutes']]

yesterday = (datetime.now() - timedelta(days=1)).date()

app.layout = html.Div([
    html.Link(rel='stylesheet', href='/assets/styles.css'),
    html.H1("Aluecor Equipment Dashboard"),
    html.Div(id='dashboard-info', children=[
        "This dashboard presents the plant equipment data for the various sections of the  plant i.e alarms, press cycles, and the aging oven."
    ]),
    html.Div(
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=yesterday,
            end_date=yesterday,
            display_format='YYYY-MM-DD',
            className='dash-date-picker'
        ),
        style={'textAlign': 'Center', 'margin': '20px 0'} 
    ),
    dcc.Graph(id='alarm-graph'),
])


@app.callback(
    Output('alarm-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_graph(start_date, end_date):
    return create_figure(start_date, end_date)


if __name__ == '__main__':
    app.run_server(debug=True)
