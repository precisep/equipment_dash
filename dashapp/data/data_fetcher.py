import os
import pandas as pd
from googleapiclient.discovery import build

def fetch_data(API_KEY, SPREADSHEET_ID):
    RANGE_ALARM_SUMMARY = 'Alarm Summary'
    RANGE_DATA_SOURCE = 'Data Source'
    service = build('sheets', 'v4', developerKey=API_KEY)

   
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

    df = df_data_source[['TSLast', 'TSActive', 'Unit Alarm Occurance']].copy()
    df['TSLast'] = pd.to_datetime(df['TSLast'], errors='coerce')
    df['TSActive'] = pd.to_datetime(df['TSActive'], errors='coerce')
    invalid_rows = df[df['TSLast'].isna() | df['TSActive'].isna()]
    if not invalid_rows.empty:
        print("Invalid datetime rows found:", invalid_rows)
    df['Time_Difference_minutes'] = (df['TSLast'] - df['TSActive']).dt.total_seconds() / 60
    df = df[['TSLast', 'TSActive','Unit Alarm Occurance', 'Time_Difference_minutes']]

   
    return df_data_source
