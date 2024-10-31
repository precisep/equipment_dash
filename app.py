import os
import pandas as pd
import dash
from dash import Dash, dcc, html, Input, Output
import requests
from dotenv import load_dotenv

# Initialize Dash app
app = Dash(__name__)
server = app.server
load_dotenv()

# Environment variables for API
api_url = os.getenv('API_URL')
authorization_token = os.getenv('AUTHORIZATION_TOKEN')

# Headers for API requests
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'token {authorization_token}'
}

# Layout of the app
app.layout = html.Div(
    className='app-container',
    children=[
        html.H1("Aluecor Alarms Dashboard", className='app-heading'),
        html.Button('Fetch Data', id='fetch-data-btn', n_clicks=0),
        html.Div(id='loading-status'),
        dcc.Loading(
            id='loading-graphs',
            type='circle',
            children=[
                html.Div(id='output-data', style={'display': 'flex', 'flex-direction': 'column'})
            ]
        ),
    ]
)

# Function to fetch data from API
def fetch_data():
    try:
        filter_query = '?fields=["tslast","tsactive","alarm","time_difference_minutes"]&limit=200000'
        response = requests.get(f'{api_url}{filter_query}', headers=headers)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {str(e)}")
        return []

# Function to parse data from the API
def parse_frappe_api():
    data = fetch_data()
    df = pd.DataFrame(data)
    print(f'Records fetched: {df.shape[0]}')  # Print number of records found
    if df.empty:
        return "No data found."
    return df.drop_duplicates()

@app.callback(
    Output('output-data', 'children'),
    Input('fetch-data-btn', 'n_clicks')
)
def update_data(n_clicks):
    if n_clicks > 0:
        df_alarms = parse_frappe_api()
        if isinstance(df_alarms, str): 
            return html.Div([html.P(df_alarms)])
        
        # Display the first few rows of the DataFrame
        return [
            html.Div([
                html.P("Data fetched from API:"),
                dcc.Markdown(df_alarms.head().to_markdown())  # Display DataFrame head in Markdown
            ])
        ]
    return []

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
