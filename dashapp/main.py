import os
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
import dash
from dash import dcc, html, Input, Output
from datetime import datetime, timedelta

from data.data_fetcher import fetch_data
from data.figure_creator import create_figure


from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('GOOGLE_API_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')


server = Flask(__name__)


app = dash.Dash(__name__, server=server, url_base_pathname='/dash/')


df_data_source= fetch_data(API_KEY, SPREADSHEET_ID)


yesterday = (datetime.now() - timedelta(days=1)).date()


app.layout = html.Div([
    html.Link(rel='stylesheet', href='/assets/styles.css'),
    html.H1("Plant Dashboard"),
    html.Div(id='dashboard-info', children=[
        "This dashboard presents the plant equipment data for the various sections of the plant i.e alarms, press cycles, and the aging oven."
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
    return create_figure(df_data_source, start_date, end_date)


if __name__ == '__main__':
    run_simple('0.0.0.0', 8050, server, use_reloader=True, use_debugger=True)
