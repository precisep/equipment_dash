import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def generate_heatmap_thermocouple(df, start_date, end_date, thermocouple):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered_df = df[start_date:end_date]

    if filtered_df.empty:
        print(f"No data available for the specified date range: {start_date} to {end_date}")
        return None  

    hourly_df = filtered_df.resample('h').mean()
    hourly_df = hourly_df.between_time('06:00', '18:00')
    heatmap_data = hourly_df[[thermocouple]].reset_index()
    heatmap_data['Date'] = heatmap_data['Version'].dt.date
    heatmap_data['Time'] = heatmap_data['Version'].dt.time
    heatmap_pivot = heatmap_data.pivot(index='Date', columns='Time', values=thermocouple)

    plt.figure(figsize=(12, 6))
    ax = sns.heatmap(heatmap_pivot, cmap='coolwarm', annot=True, fmt=".1f", cbar_kws={'label': 'Temperature (°C)'})
    ax.set_title(f'Hourly Temperature Performance of Thermocouple {thermocouple[-1]}')
    ax.set_xlabel('Time')
    ax.set_ylabel('Date')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    heatmap_filename = f"heatmap_{thermocouple[-1]}.png"
    plt.savefig(heatmap_filename)
    plt.close()  
    return heatmap_filename  
