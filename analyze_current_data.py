"""This program fetches the most recent publicly-available data
for the Indian River stream gauge. It plots the most recent 72 hours worth of 
data. It shows this data in the context of key historical slide events.

The goal of this visualization is to help put the current conditions into 
the context of what kinds of conditions have led to slides in the past.
"""

import utils.analysis_utils as a_utils
from utils import plot_utils


print("Analyzing current river data.")

current_data = a_utils.fetch_current_data(fresh=False)
readings = a_utils.process_xml_data(current_data)

recent_readings = a_utils.get_recent_readings(readings, 48)
critical_points = a_utils.get_critical_points(recent_readings)
plot_utils.plot_current_data_html(recent_readings)