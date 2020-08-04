"""Model for working with readings."""

class IRReading:

    __slots__ = ('dt_reading', 'height')


    def __init__(self, dt_reading, height):
        """Every reading has a datetime, and a height."""
        self.dt_reading = dt_reading
        self.height = height


    def get_slope(self, reading_2):
        """Calculate the slope betweent the two points.
        Return the abs value of the slope, in ft/hr.
        Assumes self is the later reading.

        DEV: Probably @staticmethod.
        """

        d_height = self.get_rise(reading_2)

        # Calculate time difference in hours.
        d_time = (reading_2.dt_reading - self.dt_reading).total_seconds() / 3600
        slope = d_height / d_time

        # print("\nCalculating slope...")
        # print(f"  Reading 1: {self.get_formatted_reading()}")
        # print(f"  Reading 2: {reading_2.get_formatted_reading()}")
        # print(d_height, d_time, slope)
        # print("---\n")

        return abs(slope)


    def get_rise(self, reading_2):
        """Calculate the rise between two points.
        Assume self is the later reading.
        """
        rise = self.height - reading_2.height
        return rise

    def get_formatted_reading(self):
        """Print a neat string of the reading."""
        dt = self.dt_reading.strftime('%m/%d/%Y %H:%M:%S')
        return f"{dt} - {self.height}"