"""Recreate the IR depth gauge graph."""
import datetime, math, csv
import sys

import pytz

from plotly.graph_objs import Scatter, Layout
from plotly import offline

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

from utils.ir_reading import IRReading
import utils.analysis_utils as a_utils
from slide_event import SlideEvent




aktz = pytz.timezone('US/Alaska')


def get_readings_weekly_format(data_file, year=None):
    """Get all readings from an IR gauge text file."""
    # DEV: This assumes akdt.
    #   Should read from file.

    print(f"\nReading data from {data_file}.")

    with open(data_file, 'r') as f:
        lines = f.readlines()
        print(f"  Read {len(lines)} lines.")
        
    # Process data.
    # Data begins on line 6.
    readings = []
    for line in lines[5:]:
        data_pieces = line.split()
        # Build datetime
        date, time = data_pieces[0], data_pieces[1]
        month, day = int(date[:2]), int(date[3:5])
        hour, minute = int(time[:2]), int(time[3:5])
        dt_ak = datetime.datetime(day=day, month=month, year=year, hour=hour,
                minute=minute)
        dt_utc = dt_ak + datetime.timedelta(hours=8)
        dt_utc = dt_utc.replace(tzinfo=pytz.utc)
        
        # Get height.
        height = float(data_pieces[2][:5])
        reading = IRReading(dt_utc, height)
        readings.append(reading)

    # Text file is in reverse chronological order; fix this.
    readings.reverse()

    print(f"  Found {len(readings)} readings.")

    return readings


def get_readings_weekly_format_utc(data_file, year=None):
    """Get all readings from an IR gauge text file."""
    # DEV: This assumes utc.
    #   Should read from file.

    print(f"\nReading data from {data_file}.")

    with open(data_file, 'r') as f:
        lines = f.readlines()
        print(f"  Read {len(lines)} lines.")
        
    # Process data.
    # Data begins on line 6.
    readings = []
    for line in lines[5:]:
        data_pieces = line.split()
        # Build datetime
        date, time = data_pieces[0], data_pieces[1]
        month, day = int(date[:2]), int(date[3:5])
        hour, minute = int(time[:2]), int(time[3:5])
        dt_utc = datetime.datetime(day=day, month=month, year=year, hour=hour,
                minute=minute)
        dt_utc = dt_utc.replace(tzinfo=pytz.utc)
        
        # Get height.
        height = float(data_pieces[2][:5])
        reading = IRReading(dt_utc, height)
        readings.append(reading)

    # Text file is in reverse chronological order; fix this.
    readings.reverse()

    print(f"  Found {len(readings)} readings.")

    return readings


def get_readings_hx_format(data_file):
    """Get all readings from an IR gauge text file.
    Uses the historical format, distinct from the weekly format:
    Date,Type Source,Stage
    0000-00-00 00:00:00,RZ,20.97
    2014-07-14 23:00:00,RZ,21.21

    These are stored in UTC.
    """

    print(f"\nReading historical data from {data_file}.")

    with open(data_file) as f:
        # First line of data is on line 5.
        reader = csv.reader(f)
        for _ in range(4):
            next(reader)
        
        readings = []
        for row in reader:
            datetime_str = row[0]
            dt = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            dt = dt.replace(tzinfo=pytz.utc)
            height = float(row[2])
            reading = IRReading(dt, height)
            readings.append(reading)
    print(f"  First reading: {readings[0].get_formatted_reading()}")

    # Text file is in chronological order.
    print(f"  Found {len(readings)} readings.")
    return readings


def get_readings_arch_format(data_file):
    """Get all readings from an IR gauge text file.
    Uses the archival format, distinct from the hx and weekly formats:
    USGS    15087700    2016-02-09 15:45    AKST    20.86   A   54.0    A

    Uses AKST and AKDT.
    """

    print(f"\nReading historical data from {data_file}.")

    with open(data_file) as f:
        # First line of data is on line 35.
        reader = csv.reader(f, delimiter='\t')
        for _ in range(34):
            next(reader)
        
        readings = []
        for row in reader:
            row = row[0].split('    ')
            # print(f"Row: {row}")
            datetime_str = row[2]
            dt_ak = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            # dt is either AKST or AKDT right now.
            tz_str = row[3]
            if tz_str == 'AKST':
                dt_utc = dt_ak + datetime.timedelta(hours=9)
            elif tz_str == 'AKDT':
                dt_utc = dt_ak + datetime.timedelta(hours=8)
            dt_utc = dt_utc.replace(tzinfo=pytz.utc)
            height = float(row[4][:5])
            reading = IRReading(dt_utc, height)
            readings.append(reading)
    print(f"  First reading: {readings[0].get_formatted_reading()}")

    # Text file is in chronological order.
    print(f"  Found {len(readings)} readings.")
    return readings


def get_relevant_slide(readings, known_slides):
    """If there's a relevant slide during this set of readings, 
    return that slide.
    Otherwise, return None.
    """
    relevant_slide = None
    for slide in known_slides:
        if readings[0].dt_reading <= slide.dt_slide <= readings[-1].dt_reading:
            print(f"Slide in range: {slide.name} - {slide.dt_slide}")
            relevant_slide = slide
            break

    return relevant_slide


def get_notification_time(critical_points, relevant_slide):
    """For a slide in a set of readings, calculate the time between the first
    critical point and the slide event.
    """
    notification_time = relevant_slide.dt_slide - critical_points[0].dt_reading
    notification_time_min = int(notification_time.total_seconds() / 60)
    print(f"Notification time: {notification_time_min} minutes")

    return notification_time_min


def plot_data(readings, critical_points=[], known_slides=[]):
    """Plot IR gauge data, with critical points in red. Known slide
    events are indicated by a vertical line at the time of the event.
    """
    # DEV: Move this to utils.plot_utils.py when possible.
    # DEV: This fn should receive any relevant slides, it shouldn't do any
    #   data processing.
    print("\nPlotting data")
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

    y_min, y_max = min_height - 0.5, max_height + 0.5

    # Is there a slide in this date range?
    relevant_slide = get_relevant_slide(readings, known_slides)
    if relevant_slide:
        try:
            notification_time = get_notification_time(critical_points, relevant_slide)
        except IndexError:
            notification_time = 0

    # Use relevant slide or first critical point to set date for title.
    if relevant_slide and critical_points:
        slide_time = relevant_slide.dt_slide.astimezone(aktz)
        title_date_str = slide_time.strftime('%m/%d/%Y')
    elif relevant_slide:
        slide_time = relevant_slide.dt_slide.astimezone(aktz)
        title_date_str = slide_time.strftime('%m/%d/%Y')
        # Also build slide label here, for slides with no critical points.
        slide_time_str = slide_time.strftime('%m/%d/%Y %H:%M:%S')
        slide_label = f"    {relevant_slide.name} - {slide_time_str}"
        slide_label += f"\n    Notification time: {notification_time} minutes"
    elif critical_points:
        dt_title = critical_points[0].dt_reading.astimezone(aktz)
        title_date_str = dt_title.strftime('%m/%d/%Y')
    else:
        dt_title = datetimes[0].dt_reading.astimezone(aktz)
        title_date_str = dt_title.strftime('%m/%d/%Y')

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

    if relevant_slide:
        slide_time_str = relevant_slide.dt_slide.astimezone(aktz).strftime(
                '%m/%d/%Y %H:%M:%S')
        data.append(
            {
                # This is a vertical line representing a slide.
                'type': 'scatter',
                'x': [str(relevant_slide.dt_slide.astimezone(aktz)), str(relevant_slide.dt_slide.astimezone(aktz))],
                'y': [y_min+0.5, y_max-0.25],
                'marker': {'color': 'green'},
                'mode': 'lines'
            }
        )
        data.append(
            {
                # Label for the slide.
                'type': 'scatter',
                'x': [str(relevant_slide.dt_slide.astimezone(aktz))],
                'y': [y_min + 1],
                'text': f'    {relevant_slide.name} - {slide_time_str}',
                'mode': 'text',
                'textposition': 'middle right'
            }
        )
        data.append(
            {
                # Label for notification time.
                'type': 'scatter',
                'x': [str(relevant_slide.dt_slide.astimezone(aktz))],
                'y': [y_min + 0.85],
                'text': f"    Notification time: {notification_time} minutes",
                'mode': 'text',
                'textposition': 'middle right'
            }
        )

    my_layout = {
        'title': f"Indian River Gauge Readings, {title_date_str}",
        'xaxis': {
                'title': 'Date/ Time',
            },
        'yaxis': {
                'title': 'River height (ft)',
                'range': [y_min, y_max]
            }
    }

    fig = {'data': data, 'layout': my_layout}
    filename = f"current_ir_plots/ir_plot_{readings[-1].dt_reading.__str__()[:10]}.html"
    offline.plot(fig, filename=filename)
    print("\nPlotted data.")


def plot_data_static(readings, critical_points=[], known_slides=[], filename=None):
    """Plot IR gauge data, with critical points in red. Known slide
    events are indicated by a vertical line at the time of the event.
    """
    # DEV: This fn should receive any relevant slides, it shouldn't do any
    #       data processing.
    #      Also, ther should be one high-level plot_data() function that
    #       takes an arg about what kind of plot to make, and then calls
    #       plot_data_interactive() or plot_data_static(), or both.

    # Matplotlib accepts datetimes as x values, so it should be handling
    #   timezones appropriately.
    datetimes = [reading.dt_reading.astimezone(aktz) for reading in readings]
    heights = [reading.height for reading in readings]

    critical_datetimes = [reading.dt_reading.astimezone(aktz) for reading in critical_points]
    critical_heights = [reading.height for reading in critical_points]

    min_height = min([reading.height for reading in readings])
    max_height = max([reading.height for reading in readings])

    y_min, y_max = min_height - 0.5, max_height + 0.5

    # Is there a slide in this date range?
    relevant_slide = get_relevant_slide(readings, known_slides)
    if relevant_slide:
        try:
            notification_time = get_notification_time(critical_points, relevant_slide)
        except IndexError:
            notification_time = 0
        else:
            # Build slide label here.
            slide_time = relevant_slide.dt_slide.astimezone(aktz)
            slide_time_str = slide_time.strftime('%m/%d/%Y %H:%M:%S')
            slide_label = f"    {relevant_slide.name} - {slide_time_str}"
            slide_label += f"\n    Notification time: {notification_time} minutes"


    # Use relevant slide or first critical point to set date for title.
    if relevant_slide and critical_points:
        dt_title = slide_time
        title_date_str = slide_time.strftime('%m/%d/%Y')
    elif relevant_slide:
        slide_time = relevant_slide.dt_slide.astimezone(aktz)
        title_date_str = slide_time.strftime('%m/%d/%Y')
        # Also build slide label here, for slides with no critical points.
        slide_time_str = slide_time.strftime('%m/%d/%Y %H:%M:%S')
        slide_label = f"    {relevant_slide.name} - {slide_time_str}"
        slide_label += f"\n    Notification time: {notification_time} minutes"
    elif critical_points:
        dt_title = critical_points[0].dt_reading.astimezone(aktz)
        title_date_str = dt_title.strftime('%m/%d/%Y')
    else:
        dt_title = datetimes[0].astimezone(aktz)
        title_date_str = dt_title.strftime('%m/%d/%Y')

    # DEV notes for building visualization:
    #   needs more times labeled on x axis;
    #   needs better format for datetimes on x axis;
    #   Thinner lines, alpha adjustment.

    # Build static plot image.
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(10, 6), dpi=128)

    # Always plot on an absolute y scale.
    ax.set_ylim([20.0, 27.5])

    # Add river heights for 48-hr period.
    ax.plot(datetimes, heights, c='blue', alpha=0.8, linewidth=1)

    # Add critical points if relevant.
    if critical_points:
        ax.plot(critical_datetimes, critical_heights, c='red', alpha=0.6,
                linewidth=1)
        ax.scatter(critical_datetimes, critical_heights, c='red', alpha=0.8,
                s=15)
        # cp_label = critical_points[0].dt_reading.astimezone(aktz).strftime(
                # '%m/%d/%Y %H:%M:%S')
        label_time = critical_points[0].dt_reading.astimezone(aktz)
        cp_label = label_time.strftime('%m/%d/%Y %H:%M:%S') + '    '
        ax.text(label_time, critical_heights[0], cp_label,
                horizontalalignment='right')

    # Add vertical line for slide if applicable.
    if relevant_slide:
        ax.axvline(x=slide_time, ymin=0.05, ymax=0.98, c='green', alpha=0.8,
                linewidth=1)
        # Label slide.
        ax.text(slide_time, y_min+1, slide_label)

    # Set chart and axes titles, and other formatting.
    # title = f"Indian River Gauge Readings, {title_date_str}"

    # This title works for animation.
    ts_title = dt_title.strftime("%H:%M:%S")
    title = f"Indian River Gauge Readings, {title_date_str}, {ts_title}"

    ax.set_title(title, loc='left')
    ax.set_xlabel('', fontsize=16)
    ax.set_ylabel("River height (ft)")



    # # Format major x ticks.
    # xaxis_maj_fmt = mdates.DateFormatter('%H:%M\n%b %d, %Y')
    # ax.xaxis.set_major_formatter(xaxis_maj_fmt)
    # # Label day every 12 hours; 0.5 corresponds to half a day
    # ax.xaxis.set_major_locator(ticker.MultipleLocator(0.5))

    # # Format minor x ticks.
    # xaxis_min_fmt = mdates.DateFormatter('%H:%M')
    # ax.xaxis.set_minor_formatter(xaxis_min_fmt)
    # # Label every 6 hours:
    # ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.25))

    # # Format dates that appear in status bar when hovering.
    # hover_fmt = mdates.DateFormatter('%H:%M  %b %d, %Y')
    # ax.fmt_xdata = hover_fmt


    # # Try building my own tick labels.
    # my_ticklabels = []
    # for dt in datetimes:
    #     dt_label = dt.strftime('%H:%M\n%b %d, %Y')

    #     times_to_label = ['00:00', '06:00', '12:00', '18:00']
    #     use_label = any(time in dt_label for time in times_to_label)

    #     if use_label:
    #         my_ticklabels.append(dt_label)
    #     else:
    #         my_ticklabels.append('')

    # # Use these tick labels.
    # ax.set_xticklabels(my_ticklabels, minor=False)


    # Make major and minor x ticks small.
    ax.tick_params(axis='x', which='both', labelsize=8)

    # DEV: Uncomment this to see interactive plots during dev work,
    #   rather than opening file images.
    # plt.show()

    # Save to file.
    if not filename:
        filename = f"current_ir_plots/ir_plot_{readings[-1].dt_reading.__str__()[:10]}.png"
    plt.savefig(filename)

    print(f"  saved: {filename}")

    # Close figure, especially helpful when rendering many frames for animation.
    plt.close('all')







if __name__ == '__main__':
    """This file can be run directly with a data file to generate a plot
    for a short period of data. The data files listed here are not included
    in the online repository, but are left here as a sample of how you might
    run this file directly.
    """
    # Load data.
    data_file = '../ir_data/irva_akdt_092019.txt'
    data_file = '../ir_data/irva_akdt_100619.txt'
    data_file = '../ir_data/irva_utc_112219.txt'
    # data_file = '../ir_data/irva_akdt_082115.txt'
    # readings = get_readings_weekly_format(data_file, 2019)
    readings = get_readings_weekly_format_utc(data_file, 2019)
    # plot_data(readings)

    # Find critical points.
    critical_points = a_utils.get_critical_points(readings)

    for cp in critical_points:
        print(cp.get_formatted_reading())

    # plot_data_critical(readings, critical_points)

    # Get known slides.
    slides_file = 'known_slides/known_slides.json'
    known_slides = SlideEvent.load_slides(slides_file)

    # Plot data, critical points, and slide event.
    plot_data(readings, critical_points, known_slides)