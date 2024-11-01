import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import plotly.io as pio
import time


pio.templates.default = "plotly_dark"

app = dash.Dash(__name__)
server = app.server
load_dotenv()

load_dotenv()

api_url = os.getenv('API_URL')
authorization_token = os.getenv('AUTHORIZATION_TOKEN')


headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'token {authorization_token}'
}


def fetch_data():
    try:
        filter_query = '?fields=["tslast","tsactive","alarm","time_difference_minutes"]&limit=200000'
        response = requests.get(f'{api_url}{filter_query}', headers=headers)
        response.raise_for_status()  
        return response.json().get('data', [])  
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {str(e)}")
        return []


def parse_frappe_api():
    data = fetch_data()
    df = pd.DataFrame(data)
    print(f'Records fetched: {df.shape[0]}')  
    return df.drop_duplicates() if not df.empty else pd.DataFrame()  


equipment_grouping = {
    'Press': ['HMI - PRESS ON HOLD'],
    'Cooling Fans': [
        'I22 - PULLER - COOLING FAN 1 - MPU',
        'I23 - PULLER - COOLING FAN 2 - MPU',
        'I24 - PULLER - COOLING FAN 3 - MPU',
        'I25 - PULLER - COOLING FAN 4 - MPU',
        'I26 - PULLER - COOLING FAN 5 - MPU',
        'I27 - PULLER - COOLING FAN 6 - MPU',
        'I28 - PULLER - COOLING FAN 7 - MPU',
        'I29 - PULLER - COOLING FAN 8 - MPU',
        'I30 - PULLER - COOLING FAN 9 - MPU',
        'I31 - PULLER - COOLING FAN 10 - MPU',
        'I32 - PULLER - COOLING FAN 11 - MPU'
    ],
    'Gas Oven Burners': [
        'I43 - GAS OVEN - BURNER 1 FAULT',
        'I44 - GAS OVEN - BURNER 2 FAULT',
        'I45 - GAS OVEN - BURNER 3 FAULT',
        'I46 - GAS OVEN - BURNER 4 FAULT',
        'I47 - GAS OVEN - BURNER 5 FAULT',
        'I48 - GAS OVEN - BURNER 6 FAULT',
        'I49 - GAS OVEN - BURNER 7 FAULT',
        'I50 - GAS OVEN - BURNER 8 FAULT',
        'I51 - GAS OVEN - BURNER 9 FAULT',
        'I52 - GAS OVEN - BURNER 10 FAULT'
    ],
    'Pumps': [
        'I03 - BOTTOM OIL CIRCULATION PUMP - MPU',
        'I13 - COOLING TOWER - WATER TOWER 2 PUMP - MPU',
        'I14 - COOLING TOWER - SMALL BLUE MIDDLE PUMP - MPU',
        'I15 - COOLING TOWER - BIG WATER PUMP - MPU',
        'I100 - MAIN PUMP 2 - MPU',
        'I102 - MAIN PUMP 1 - MPU'
    ],
    'Puller System': [
        'PULLER ENCODER COMS DOWN',
        'PULLER DRIVE COMS DOWN',
        'PULLER PANEL IO COMS DOWN',
        'I04 - PULLER - PLATEN SAW - MPU',
        'I18 - PULLER - HYDRAULIC POWER PACK SMALL ORANGE MOTOR FOR SLAT TABLE - MPU',
        'I53 - PULLER - SAFETY GATE PAUSE REVERSE',
        '9400 - PULLER DRIVE FAULT',
        'I33 - PULLER - EXTRACTION FAN 1 - MPU',
        'I34 - PULLER - EXTRACTION FAN 2 - MPU',
        'I35 - PULLER - EXTRACTION FAN 3 - MPU'
    ],
    'Safety Systems': [
        'I191 - PRESS - SAFETY FAULT ( E-STOP / PULL ROPE)',
        'I192 - PROFILE CUTTER - E-STOP FAULT',
        'SAFETIES NOT HEALTHY - RESET FAULTS',
        'MAIN PANEL IO COMS DOWN',
        'I38 - MAIN DESK E-STOP',
        'I105 - BILLET CUTTER - ELEVATOR E-STOP'
    ],
    'Induction Heater': [
        'I109 - INDUCTION HEATER TRANSFORMER OVER TEMPERATURE',
        'I107 - INDUCTION HEATER THERMISTOR OVER TEMPERATURE - ON'
    ],
    'Transfer System': [
        'I05 - TRANSFER - BILLET TROLLEY - MPU',
        'I07 - TRANSFER - INDUCTION HEATER EXIT ROLLS - MPU',
        'I08 - TRANSFER - GAS OVEN ENTRY ROLLS - MPU',
        'I09 - TRANSFER - GAS OVEN EXIT ROLLS - MPU',
        'I10 - TRANSFER - BILLET ELEVATOR - MPU'
    ],
    'Profile Cutter':[
        'I01 - PROFILE CUTTER - SAW - MPU',
        'I11 - PROFILE CUTTER - MPU - OUTFEED TABLE BELT',
        'I12 - PROFILE CUTTER - MPU - HYDRAULIC MOTOR',
        'I16 - PROFILE CUTTER - MPU - INFEED ROLLER 1',
        'I17 - PROFILE CUTTER - MPU - INFEED ROLLER 2',
    ],
    'Container':[
        'CONTAINER ELEMENT PHASE 1 UNDER CURRENT',
        'CONTAINER ELEMENT PHASE 2 UNDER CURRENT',
        'CONTAINER ELEMENT PHASE 3 UNDER CURRENT',
        'I37 - CONTAINER SEAL PUMP - MPU',
    ],
    'Miscellaneous': [
        '0',
        'BILLET PLC INTERCOMS DOWN',
        'I02 - Spare - MPU',
        'I19 - STRETCHER - HYDRAULIC BIG ORANGE MOTOR BIG - MPU',
        'I20 - Spare - MPU',
        'I36 - BLOWER MOTOR - MPU',
        'I79 - ONE OF THE OIL SUPPLY HAND VALVE 1,2,3 ARE NOT FULLY OPEN',
    ]}


def map_to_equipment_group(alarm, equipment_grouping):
    for equipment, alarms in equipment_grouping.items():
        if alarm in alarms:
            return equipment
    return 'Unknown'


def minutes_to_hhmm(minutes):
    hours = int(minutes // 60)
    mins = int(minutes % 60)
 

    if hours > 0 and mins > 0:
        return f'{hours} hour{"s" if hours > 1 else ""} {mins} minute{"s" if mins > 1 else ""}'
    elif hours > 0:
        return f'{hours} hour{"s" if hours > 1 else ""}'
    else:
        return f'{mins} minute{"s" if mins > 1 else ""}'



def create_figure(selected_date,df):
    start_date = f"{selected_date} 07:00:00"
    end_date = f"{selected_date} 17:00:00"
    
   
    start_date_filter = pd.to_datetime(start_date)
    end_date_filter = pd.to_datetime(end_date)

    df['tslast'] = pd.to_datetime(df['tslast'], errors='coerce')
    df['tsactive'] = pd.to_datetime(df['tsactive'], errors='coerce')
    
    mask = (df['tslast'] >= start_date_filter) & (df['tslast'] < end_date_filter)
    filtered_df = df[mask]

    filtered_df['Equipment Group'] = filtered_df['alarm'].apply(lambda alarm: map_to_equipment_group(alarm, equipment_grouping)).dropna()

    alarm_downtime_totals = filtered_df.groupby(['Equipment Group'])['time_difference_minutes'].sum().reset_index()

    alarm_downtime_totals = alarm_downtime_totals.sort_values('time_difference_minutes', ascending=False)
    filtered_df['Equipment Group'] = pd.Categorical(filtered_df['Equipment Group'], categories=alarm_downtime_totals['Equipment Group'], ordered=True)
    filtered_df = filtered_df.sort_values('Equipment Group', ascending=False)
    filtered_df['tslast'] = pd.to_datetime(filtered_df['tslast'])
    time_range = pd.date_range(start=start_date, end=end_date, freq='h')

    alarm_group = filtered_df['Equipment Group'].unique()

    fig = go.Figure()

    bar_width = 0.25

    for equipment_group in alarm_group:
        alarm_data = filtered_df[filtered_df['Equipment Group'] == equipment_group]
        last_time = pd.Timestamp(start_date)

        for hour in time_range:
            active_alarms = alarm_data[(alarm_data['tslast'] >= last_time) & (alarm_data['tslast'] < hour)]
            downtime_total = active_alarms['time_difference_minutes'].sum()
            alarms_list = active_alarms['alarm'].unique()

            if downtime_total > 0:
                if (hour - last_time).total_seconds() / 60 > 0:
                    active_time = (hour - last_time).total_seconds() / 60 - downtime_total
                    start_time = active_alarms['tsactive'].iloc[0] if not active_alarms.empty else last_time

                    
                    start_time_in_minutes = (start_time - pd.Timestamp(start_time.date())).total_seconds() / 60
                    
                    alarms_hover = "<br>".join(alarms_list)

                    fig.add_trace(go.Bar(
                        y=[equipment_group],
                        x=[active_time],
                        width=bar_width,
                        orientation='h',
                        name='Good State',
                        marker_color='lightgreen',
                        base=last_time.hour * 60 + last_time.minute,
                        hovertemplate=f'Start Time: {start_time.strftime("%Y-%m-%d %H:%M")} <br>Equipment: {equipment_group} Type: Good State<br>Duration: {minutes_to_hhmm(round(active_time, 2))}<extra></extra>',
                        showlegend=False
                    ))

                    fig.add_trace(go.Bar(
                        y=[equipment_group],
                        x=[downtime_total],
                        width=bar_width,
                        orientation='h',
                        name='Active Alarm',
                        marker_color='red',
                        base=last_time.hour * 60 + last_time.minute + active_time,
                        hovertemplate=f'Start Time: {start_time.strftime("%Y-%m-%d %H:%M")} <br>Equipment: {equipment_group} <br>Alarms: {alarms_hover}<br>Type: Active Alarm<br>Duration: {minutes_to_hhmm(round(downtime_total, 2))}<extra></extra>',
                        showlegend=False
                    ))
                last_time = hour


        if last_time < time_range[-1]:
            remaining_time = (time_range[-1] - last_time).total_seconds() / 60
            fig.add_trace(go.Bar(
                y=[equipment_group],
                x=[remaining_time],
                width=bar_width,
                orientation='h',
                name='Good State',
                marker_color='lightgreen',
                base=last_time.hour * 60 + last_time.minute,
                hovertemplate=f'Equipment: {equipment_group} <br>Alarms: None<br>Type: Good State<br>Duration: {minutes_to_hhmm(round(remaining_time, 2))}<extra></extra>',
                showlegend=False
            ))

        
    date_min = filtered_df['tslast'].min().replace(hour=7, minute=0, second=0)
    date_max = filtered_df['tslast'].max().replace(hour=17, minute=0, second=0)

    
    fig.update_layout(
        title="Active Alarm and Good State Duration by Alarm and Equipment Group",
        xaxis_title="Timstamp",
        yaxis_title="Equipment Group and Alarm",
        barmode='stack',
        height=750,
        xaxis=dict(
            tickmode='array',
            tickvals=[(hour.hour * 60) for hour in time_range],
            ticktext=[hour.strftime('%Y-%m-%d %H:%M') for hour in time_range],
            showgrid=True
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
        "This dashboard presents the alarms data for the plant equipment."
    ]),
    html.Div(
        dcc.DatePickerSingle(
        id='date-picker',
        date=yesterday,
        display_format='YYYY-MM-DD',
        style={'margin': '20px'}
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
    [Input('date-picker', 'date')]
)
def update_graph(selected_date):
    df_alarms = parse_frappe_api()
    if selected_date is not None:
        fig = create_figure(selected_date,df_alarms)
        return fig
    return go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)
