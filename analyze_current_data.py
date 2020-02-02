"""This program fetches the most recent publicly-available data
for the Indian River stream gauge. It plots the most recent 72 hours worth of 
data. It shows this data in the context of key historical slide events.

The goal of this visualization is to help put the current conditions into 
the context of what kinds of conditions have led to slides in the past.
"""

import sys, datetime

from xml.etree import ElementTree as ET

import requests, pytz

import utils.analysis_utils as a_utils
from utils.ir_reading import IRReading
from utils import plot_utils


def fetch_current_data(fresh=True, filename='ir_data_other/current_data.txt'):
    """Fetches current data from the river gauge.

    If fresh is False, looks for cached data.
      Cached data is really just for development purposes, to avoid hitting
      the server unnecessarily.

    Returns the current data as text.
    """
    print("  Fetching data...")
    if fresh:
        print("    Fetching fresh gauge data...")

        gauge_url = "https://water.weather.gov/ahps2/hydrograph_to_xml.php?gage=irva2&output=tabular"
        gauge_url_xml = "https://water.weather.gov/ahps2/hydrograph_to_xml.php?gage=irva2&output=xml"
        r = requests.get(gauge_url_xml)
        print(f"    Response status: {r.status_code}")
        # return r

        with open(filename, 'w') as f:
            f.write(r.text)
        print(f"    Wrote data to {filename}.")

        return r.text

    else:
        # Try to use cached data.
        try:
            with open(filename) as f:
                current_data = f.read()
        except:
            # Can't read from file, so fetch fresh data.
            print("    Couldn't read from file, fetching fresh data...")
            return fetch_current_data(fresh=True)
        else:
            print("    Read gauge data from file.")
            return current_data


def process_xml_data(data):
    """Processes xml data from text file.
    Returns a list of readings.
    """
    print("  Processing raw data...")
    # Parse xml tree from file.
    root = ET.fromstring(current_data)
    tree = ET.ElementTree(root)

    # 6th element is the set of observed readings.
    # 1st and 2nd elements of each reading are datetime, height.
    readings = []
    for reading in root[5]:
        dt_reading_str = reading[0].text
        dt_reading = datetime.datetime.strptime(dt_reading_str,
                 "%Y-%m-%dT%H:%M:%S-00:00")
        dt_reading_utc = dt_reading.replace(tzinfo=pytz.utc)
        height = float(reading[1].text)

        reading = IRReading(dt_reading_utc, height)
        readings.append(reading)

    # Readings need to be in chronological order.
    # DEV: This should be an absolute ordering, not just relying on 
    #      input file format.
    readings.reverse()

    print(f"    Found {len(readings)} readings.")
    return readings


def get_recent_readings(readings, hours_lookback):
    """From a set of readings, return only the most recent x hours
    of readings.
    """
    pass
    # Get datetime of most recent reading in set.
    # Get datetime to start with.
    # Build new list of readings that are between these values.
    # Return this list.
    print(f"  Getting most recent {hours_lookback} hours of readings...")
    last_reading = readings[-1]
    print(last_reading.dt_reading)

    td_lookback = datetime.timedelta(hours=hours_lookback)
    dt_first_reading = last_reading.dt_reading - td_lookback
    print(dt_first_reading)
    recent_readings = [r for r in readings
                            if r.dt_reading >= dt_first_reading]
    print(f"    Found {len(recent_readings)} recent readings.")
    print(recent_readings[0].dt_reading, recent_readings[-1].dt_reading)
    return recent_readings







if __name__ == '__main__':
    print("Analyzing current river data.")

    current_data = fetch_current_data(fresh=False)
    readings = process_xml_data(current_data)
    critical_points = a_utils.get_critical_points(readings)
    # plot_utils.plot_current_data_html(readings)
    recent_readings = get_recent_readings(readings, 72)