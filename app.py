import os
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set API URL and Authorization token from .env
api_url = os.getenv('API_URL')
authorization_token = os.getenv('AUTHORIZATION_TOKEN')

# Set headers for the API request
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'token {authorization_token}'
}

# Function to fetch data from the API
def fetch_data():
    try:
        filter_query = '?fields=["tslast","tsactive","alarm","time_difference_minutes"]&limit=200000'
        response = requests.get(f'{api_url}{filter_query}', headers=headers)
        response.raise_for_status()  # Check for request errors
        return response.json().get('data', [])  # Get 'data' field if available
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {str(e)}")
        return []

# Parse data into a DataFrame
def parse_frappe_api():
    data = fetch_data()
    df = pd.DataFrame(data)
    print(f'Records fetched: {df.shape[0]}')  # Print number of records
    return df.drop_duplicates() if not df.empty else pd.DataFrame()  # Remove duplicates if any

# Fetch and display the data
df_alarms = parse_frappe_api()
print(df_alarms.head())  # Display the first few rows of the DataFrame
