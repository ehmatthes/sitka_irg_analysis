"""Utilities for plotting stream gauge data.
"""

import pytz

from plotly.graph_objs import Scatter, Layout
from plotly import offline


aktz = pytz.timezone('US/Alaska')


def plot_current_data_html(readings, critical_points=[], known_slides=[],
        filename=None):
    """Plot IR gauge data, with critical points in red. Known slide
    events are indicated by a vertical line at the time of the event.
    """
    # DEV: This fn should receive any relevant slides, it shouldn't do any
    #   data processing.
    print("\n  Plotting current data")
    if critical_points:
        print(f"First critical point: {critical_points[0].get_formatted_reading()}")

    # Plotly considers everything UTC. Send it strings, and it will
    #  plot the dates as they read.
    datetimes = [str(reading.dt_reading.astimezone(aktz)) for reading in readings]
    heights = [reading.height for reading in readings]

    critical_datetimes = [str(reading.dt_reading.astimezone(aktz)) for reading in critical_points]
    critical_heights = [reading.height for reading in critical_points]

    min_height = min([reading.height for reading in readings])
    max_height = max([reading.height for reading in readings])

    # Want current data to be plotted with a consistent scale on the y axis.
    y_min, y_max = 20.0, 27.5

    # Set date string for chart title.
    dt_title = readings[0].dt_reading.astimezone(aktz)
    title_date_str = dt_title.strftime('%m/%d/%Y')

    # Set filename.
    if not filename:
        filename = f"ir_plot_{readings[-1].dt_reading.__str__()[:10]}.html"

    data = [
        {
            # Non-critical gauge height data.
            'type': 'scatter',
            'x': datetimes,
            'y': heights
        }
    ]
    if critical_points:
        label_dt_str = critical_points[0].dt_reading.astimezone(aktz).strftime(
                '%m/%d/%Y %H:%M:%S')
        data.append(
            {
                # Critical points.
                'type': 'scatter',
                'x': critical_datetimes,
                'y': critical_heights,
                'marker': {'color': 'red'}
            }
        )
        data.append(
            {
                # Label for first critical point.
                'type': 'scatter',
                'x': [critical_datetimes[0]],
                'y': [critical_heights[0]],
                'text': f"{label_dt_str}  ",
                'mode': 'text',
                'textposition': 'middle left'
            }
        )

    my_layout = {
        'title': f"Current Indian River Gauge Readings, {title_date_str}",
        'xaxis': {
                'title': 'Date/ Time',
            },
        'yaxis': {
                'title': 'River height (ft)',
                'range': [y_min, y_max]
            }
    }

    fig = {'data': data, 'layout': my_layout}
    offline.plot(fig, filename=filename)
    print("\n    Plotted data.")