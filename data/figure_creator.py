import pandas as pd
import plotly.graph_objects as go

def create_figure(start_date, end_date):
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
       # plot_bgcolor='#36454F',
       # paper_bgcolor='#36454F',
        font=dict(color='white')
    )

  
    fig.add_trace(go.Bar(
        name='Good State',
        marker_color='lightgreen',
        hovertemplate='Type: Good State<extra></extra>',
        showlegend=True,
        visible='legendonly'
    ))

    fig.add_trace(go.Bar(
        name='Active Alarm',
        marker_color='red',
        hovertemplate='Type: Active Alarm<extra></extra>',
        showlegend=True,
        visible='legendonly'
    ))

    return fig
