"""Process all historical IR gauge data.
How many slides have were preceded by a critical point?
What do the notification times look like?
How many false positives were there?
How many notifications would have been issued over a 5-year period?
How many slides were not preceded by a critical point?
Was there anything special about those slides?
What did the river data look like for those slides?
"""
import math
import sys

import plot_heights as ph
from slide_event import SlideEvent
import utils.analysis_utils as a_utils
from utils.analysis_utils import RISE_CRITICAL, M_CRITICAL


def get_first_critical_points(readings):
    """From a long set of data, find the first critical reading in
    each potentially critical event.
    Return this set of readings.
    """
    print("\nLooking for first critical points...")

    # What's the longest it could take to reach critical?
    #   RISE_CRITICAL / M_CRITICAL
    #  If it rises faster than that, we want to know.
    #    Multiplied by 4, because there are 4 readings/hr.
    # Determine readings/hr from successive readings.
    #  reading_interval is in minutes
    # Assumes all readings in this set of readings are at a consistent interval.
    reading_interval = (readings[1].dt_reading - readings[0].dt_reading).total_seconds() // 60
    lookback_factor = int(60 / reading_interval)
    # print('lf', lookback_factor)
    max_lookback = math.ceil(RISE_CRITICAL / M_CRITICAL) * lookback_factor

    first_critical_points = []
    # Start with 10th reading, so can look back.
    for reading_index, reading in enumerate(readings[max_lookback:]):
        # print(f"  Examining reading: {reading.get_formatted_reading()}")
        # Get prev max_lookback readings.
        prev_readings = [reading for reading in readings[reading_index-max_lookback:reading_index]]
        for prev_reading in prev_readings:
            rise = reading.get_rise(prev_reading)
            m = reading.get_slope(prev_reading)
            # print(f"    Rise: {rise} Slope: {m}")
            if rise >= RISE_CRITICAL and m > M_CRITICAL:
                # print(f"Critical point: {reading.get_formatted_reading()}")
                # Ignore points 12 hours after an existing critical point.
                if not first_critical_points:
                    first_critical_points.append(reading)
                    break
                elif (reading.dt_reading - first_critical_points[-1].dt_reading).total_seconds() // 3600 > 12:
                    first_critical_points.append(reading)
                    break
                else:
                    # This is shortly after an already-identified point.
                    break

    return first_critical_points


def get_48hr_readings(first_critical_point):
    """Return 24 hrs of readings before, and 24 hrs of readings after the
    first critical point."""
    readings_per_hr = a_utils.get_reading_rate(all_readings)
    # Pull from all_readings, with indices going back 24 hrs and forward
    #  24 hrs.
    fcp_index = all_readings.index(first_critical_point)
    start_index = fcp_index - 24 * readings_per_hr
    end_index = fcp_index + 24 * readings_per_hr
    # print(readings_per_hr, start_index, end_index)

    return all_readings[start_index:end_index]

def get_slides_in_range(known_slides, readings):
    """Return a list of the slides that occurred during this set of readings.
    """
    start = readings[0].dt_reading
    end = readings[-1].dt_reading
    return [slide for slide in known_slides if start <= slide.dt_slide <= end]


if __name__ == '__main__':
    """Run this file directly to generate a new set of plots for the entire
    historical period for the data included in ir_data_clean/.
    """

    # Make sure to call the correct parsing function for the data file format.
    # Data analysis is data cleaning. :/
    # DEV: Should probably walk the ir_data_clean directory, instead of making
    #      this list manually.
    data_files = [
        'ir_data_clean/irva_utc_072014-022016_hx_format.txt',
        'ir_data_clean/irva_akdt_022016-102019_arch_format.txt',
    ]

    # Get known slides.
    slides_file = 'known_slides/known_slides.json'
    known_slides = SlideEvent.load_slides(slides_file)

    # Track overall stats.
    #   How many notifications followed by slides?
    #   How many notifications not followed by slides?
    #   How many slides were not missed?
    notifications_issued = 0
    associated_notifications = 0
    unassociated_notifications = 0
    unassociated_notification_points = []
    relevant_slides = []
    unassociated_slides = []
    notification_times = {}
    earliest_reading, latest_reading = None, None
    plots_generated = 0

    for data_file in data_files:
        # Use proper parsing function.
        if 'hx_format' in data_file:
            all_readings = ph.get_readings_hx_format(data_file)
        elif 'arch_format' in data_file:
            all_readings = ph.get_readings_arch_format(data_file)

        # Keep track of earliest and latest reading across all data files.
        if not earliest_reading:
            earliest_reading = all_readings[0]
            latest_reading = all_readings[-1]
        else:
            if all_readings[0].dt_reading < earliest_reading.dt_reading:
                earliest_reading = all_readings[0]
            if all_readings[-1].dt_reading > latest_reading.dt_reading:
                latest_reading = all_readings[-1]

        # Get all the known slides that occurred during these readings.
        slides_in_range = get_slides_in_range(known_slides, all_readings)

        # Find the start of all critical periods in this data file.
        first_critical_points = get_first_critical_points(all_readings)
        for reading in first_critical_points:
            print(reading.get_formatted_reading())
        notifications_issued += len(first_critical_points)

        # reading_sets is a list of lists. Each list is a set of readings to plot,
        #   based around a first critical point.
        reading_sets = [get_48hr_readings(fcp) for fcp in first_critical_points]

        for reading_set in reading_sets:
            critical_points = a_utils.get_critical_points(reading_set)
            relevant_slide = ph.get_relevant_slide(reading_set, known_slides)
            if relevant_slide:
                relevant_slides.append(relevant_slide)
                associated_notifications += 1
                notification_time = ph.get_notification_time(critical_points,
                        relevant_slide)
                notification_times[relevant_slide] = notification_time
                # Remove this slide from slides_in_range, so we'll
                #   be left with unassociated slides.
                slides_in_range.remove(relevant_slide)
            else:
                # This may be an unassociated notification.
                unassociated_notification_points.append(critical_points[0])
                unassociated_notifications += 1

            # Plot data, critical points, and slide event.
            ph.plot_data(reading_set, critical_points, known_slides)
            ph.plot_data_static(reading_set, critical_points,
                    known_slides=known_slides)
            plots_generated += 1

        # Any slides left in slides_in_range are unassociated.
        #   We can grab a 48-hr data set around this slide.
        for slide in slides_in_range:
            # Get first reading after this slide, and base 48 hrs around that.
            for reading in all_readings:
                if reading.dt_reading > slide.dt_slide:
                    slide_readings = get_48hr_readings(reading)
                    break

            print(f"\nPlotting data for unassociated slide: {slide.name}")
            ph.plot_data(slide_readings, known_slides=known_slides)
            ph.plot_data_static(slide_readings, known_slides=known_slides)

            unassociated_slides.append(slide)


        # Plot 48-hr periods for any slides from this time period that
        #   were not caught.

    # Summarize results.
    assert(unassociated_notifications == len(unassociated_notification_points))
    unassociated_slides = set(known_slides) - set(relevant_slides)
    slides_outside_range = []
    for slide in known_slides:
        if ( (slide.dt_slide < earliest_reading.dt_reading)
                 or (slide.dt_slide > latest_reading.dt_reading) ):
            unassociated_slides.remove(slide)
            slides_outside_range.append(slide)
    start_str = earliest_reading.dt_reading.strftime('%m/%d/%Y')
    end_str = latest_reading.dt_reading.strftime('%m/%d/%Y')
    print("\n\n --- Final Results ---\n")
    print(f"Data analyzed from: {start_str} to {end_str}")
    print(f"  Critical rise used: {RISE_CRITICAL} feet")
    print(f"  Critical rise rate used: {M_CRITICAL} ft/hr")
    print(f"  {plots_generated} plots generated")

    print(f"\nNotifications Issued: {notifications_issued}")
    print(f"\nTrue Positives: {associated_notifications}")
    for slide in relevant_slides:
        print(f"  {slide.name} - Notification time: {notification_times[slide]} minutes")
    print(f"\nFalse Positives: {unassociated_notifications}")
    for notification_point in unassociated_notification_points:
        print(f"  {notification_point.dt_reading.strftime('%m/%d/%Y %H:%M:%S')}")

    print(f"\nFalse Negatives: {len(unassociated_slides)}")
    for slide in unassociated_slides:
        print(f"  {slide.name}")
    print(f"\nSlides outside range: {len(slides_outside_range)}")
    for slide in slides_outside_range:
        print(f"  {slide.name}")

