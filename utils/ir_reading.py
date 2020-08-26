"""Model for working with Indian River stream gauge readings."""

from collections import namedtuple


IRReading = namedtuple('IRReading', ['dt_reading', 'height'])


def get_slope(reading, reading_2):
    """Calculate the slope between the two points.
    Return the abs value of the slope, in ft/hr.
    Assumes reading_2 is the earlier reading.
    """

    d_height = reading.height - reading_2.height
    # Calculate time difference in hours.
    d_time = (reading.dt_reading - reading_2.dt_reading).total_seconds() / 3600
    slope = d_height / d_time

    return abs(slope)

def get_rise(reading, reading_2):
    """Calculate the rise between two points.
    Assume reading_2 is the earlier reading.
    """
    return reading.height - reading_2.height

def get_formatted_reading(reading):
    """Print a neat string of the reading."""
    dt = reading.dt_reading.strftime('%m/%d/%Y %H:%M:%S')
    return f"{dt} - {reading.height}"