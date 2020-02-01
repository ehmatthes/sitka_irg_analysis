"""This program fetches the most recent publicly-available data
for the Indian River stream gauge. It plots the most recent 72 hours worth of 
data. It shows this data in the context of key historical slide events.

The goal of this visualization is to help put the current conditions into 
the context of what kinds of conditions have led to slides in the past.
"""

import sys

from xml.etree import ElementTree as ET

import requests


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
    Returns? Sets?
    """
    print("  Processing raw data...")
    # Parse xml tree from file.
    root = ET.fromstring(current_data)
    tree = ET.ElementTree(root)

    # 6th element is the set of observed readings.
    # 1st and 2nd elements of each reading are datetime, height.
    for reading in root[5][:3]:
        dt_reading_str = reading[0].text
        height = float(reading[1].text)
        print(f"The river was at {height} at {dt_reading_str}.")






if __name__ == '__main__':
    print("Analyzing current river data.")
    current_data = fetch_current_data(fresh=False)

    process_xml_data(current_data)