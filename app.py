import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from flask import Flask
from dotenv import load_dotenv
import plotly.io as pio
import time


pio.templates.default = "plotly_dark"

app = dash.Dash(__name__)
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

def create_figure(start_date, end_date):
    time.sleep(3)
    
    mask = (df['TSLast'] >= start_date) & (df['TSLast'] <= end_date)
    filtered_df = df[mask]
    alarm_downtime_totals = filtered_df.groupby('Alarm')['Time_Difference_minutes'].sum().reset_index()
    alarm_downtime_totals = alarm_downtime_totals.sort_values('Time_Difference_minutes', ascending=False)
    filtered_df['Alarm'] = pd.Categorical(filtered_df['Alarm'], categories=alarm_downtime_totals['Alarm'], ordered=True)
    filtered_df = filtered_df.sort_values('Alarm', ascending=False)
    filtered_df['TSLast'] = pd.to_datetime(filtered_df['TSLast'])
    time_range = pd.date_range(start=start_date, end=end_date, freq='h')
    alarms = filtered_df['Alarm'].unique()
    fig = go.Figure()

    bar_width = 0.65

    for alarm in alarms:
        alarm_data = filtered_df[filtered_df['Alarm'] == alarm]
        last_time = pd.Timestamp(start_date)

        for hour in time_range:
            downtime_segment = alarm_data[(alarm_data['TSLast'] >= last_time) & (alarm_data['TSLast'] < hour)]
            downtime_total = downtime_segment['Time_Difference_minutes'].sum()

            if downtime_total > 0:
                if (hour - last_time).total_seconds() / 60 > 0:
                    active_time = (hour - last_time).total_seconds() / 60 - downtime_total
                    start_time = downtime_segment['TSActive'].iloc[0] if not downtime_segment.empty else last_time
                    fig.add_trace(go.Bar(
                        y=[alarm],
                        x=[active_time],
                        width=bar_width,
                        orientation='h',
                        name='Good State',
                        marker_color='lightgreen',
                        base=last_time.hour * 60 + last_time.minute,
                        hovertemplate=f'Start Time: {start_time} <br>Alarm:  {alarm}  <br>Type: Good State<br>Duration: {round(active_time, 2)}minutes<extra></extra>',
                        showlegend=False  
                    ))
                    fig.add_trace(go.Bar(
                        y=[alarm],
                        x=[downtime_total],
                        width=bar_width,
                        orientation='h',
                        name='Active Alarm',
                        marker_color='red',
                        base=last_time.hour * 60 + last_time.minute + active_time,
                        hovertemplate=f'Start Time: {start_time} <br>Alarm: {alarm}<br>Type: Active Alarm<br>Duration: {round(downtime_total, 2)} minutes<extra></extra>',
                        showlegend=False  
                    ))
                last_time = hour

        if last_time < time_range[-1]:
            remaining_time = (time_range[-1] - last_time).total_seconds() / 60
            fig.add_trace(go.Bar(
                y=[alarm],
                x=[remaining_time],
                width=bar_width,
                orientation='h',
                name='Good State',
                marker_color='lightgreen',
                base=last_time.hour * 60 + last_time.minute,
                hovertemplate='Alarm: ' + alarm + '<br>Type: Good State<br>Duration: ' + str(round(remaining_time, 2)) + ' minutes<extra></extra>',
                showlegend= False
            ))

    fig.update_layout(
        title="Active Alarm and Good State Duration by Alarm",
        xaxis_title="Time (Hours)",
        yaxis_title="Alarm",
        barmode='stack',
        height=2000,
        xaxis=dict(
            tickmode='array',
            tickvals=[(hour.hour * 60) for hour in time_range],
            ticktext=[hour.strftime('%Y-%m-%d %H:%M') for hour in time_range],
            showgrid=True,
            title_font_size=12
        ),
        yaxis=dict(tickfont=dict(size=10)),
        font=dict(color='white')
    )

    return fig

yesterday = (datetime.now() - timedelta(days=1)).date()

app.layout = html.Div([
    html.Link(rel='stylesheet', href='/assets/styles.css'),
    html.H1("Aluecor Equipment Dashboard"),
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
    dcc.Loading(
        id="loading-spinner",
        type="circle",  
        children=[
            dcc.Graph(id='alarm-graph')
        ],
        fullscreen=True  
    )
])

@app.callback(
    Output('alarm-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
)
def update_graph(start_date, end_date):
    return create_figure(start_date, end_date)

if __name__ == '__main__':
    app.run_server(debug=True)
