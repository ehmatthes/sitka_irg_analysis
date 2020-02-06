"""This program varies the values of CRITICAL_RISE and M_CRITICAL.
The goal is find optimal parameters that minimize the number of false
positives, while keeeping the true positives. It also keeps track of 
notification times. A perfect TP/FP outcome with minimal notification time
is useless.

Output is a list of dicts; each dict contains the values for that trial: 
critical_rise, m_critical, tp/fp/fn, and a name for the series. These results
can be analyzed in a separate file.

This file will take a while to run, especially with the current naive
processing approach. So, developing visualizations of this data will be much
easier if they can be done separately from the work of varying the critical 
parameters.

IMPORTANT: Can't trust this fully until further validation of known slides.
For example, Starrigavan slide should be evaluated, and known slides should
be confirmed against an existing list.
"""

import sys, string

# DEV: The functions used from plot_heights should be moved to utils.
import plot_heights as ph
from slide_event import SlideEvent
import utils.analysis_utils as a_utils
from utils.analysis_utils import RISE_CRITICAL, M_CRITICAL

# Intervals over which to iterate 
rc_interval = 0.5
mc_interval = 0.25


def analyze_all_data(rise_critical, m_critical, verbose=False, 
        all_results=[], alpha_name=''):
    # DEV: This is an abuse of Python norms. All caps should be constants. :(
    a_utils.RISE_CRITICAL = rise_critical
    a_utils.M_CRITICAL = m_critical

    # Make sure to call the correct parsing function for the data file format.
    # Data analysis is data cleaning. :/
    # DEV: Should probably walk the ir_data_clean directory, instead of making
    #      this list manually.
    # DEV: Should generate a JSON file of IRReading objects, and not have to
    #      parse this data set.
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
        slides_in_range = a_utils.get_slides_in_range(
                known_slides, all_readings)

        # Find the start of all critical periods in this data file.
        first_critical_points = a_utils.get_first_critical_points(all_readings)
        for reading in first_critical_points:
            print(reading.get_formatted_reading())
        notifications_issued += len(first_critical_points)

        # reading_sets is a list of lists. Each list is a set of readings to
        #   plot or analyze, based around a first critical point.
        reading_sets = [a_utils.get_48hr_readings(fcp, all_readings)
                                        for fcp in first_critical_points]

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

        # Any slides left in slides_in_range are unassociated.
        #   We can grab a 48-hr data set around this slide.
        for slide in slides_in_range:
            # Get first reading after this slide, and base 48 hrs around that.
            for reading in all_readings:
                if reading.dt_reading > slide.dt_slide:
                    slide_readings = a_utils.get_48hr_readings(
                            reading, all_readings)
                    break
            unassociated_slides.append(slide)

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
    if verbose:
        print("\n\n --- Final Results ---\n")
        print(f"Data analyzed from: {start_str} to {end_str}")
        print(f"  Critical rise used: {a_utils.RISE_CRITICAL} feet")
        print(f"  Critical rise rate used: {a_utils.M_CRITICAL} ft/hr")

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


    # Build results dict here, and add to file.
    results_dict = {
        'alpha name': alpha_name,
        'name': f"{a_utils.RISE_CRITICAL}_{a_utils.M_CRITICAL}",
        'critical rise': a_utils.RISE_CRITICAL,
        'critical slope': a_utils.M_CRITICAL,
        'true positives': associated_notifications,
        'false postives': unassociated_notifications,
        'false negatives': len(unassociated_slides),
        'notification times': list(notification_times.values()),
    }

    all_results.append(results_dict)


if __name__ == '__main__':
    all_results = []
    alpha_names = list(string.ascii_uppercase)
    alpha_name = alpha_names.pop(0)

    rise_critical = 2.5
    m_critical = 0.5

    analyze_all_data(rise_critical=rise_critical, m_critical=m_critical,
        all_results=all_results, alpha_name=alpha_name)

    print(all_results)

    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(all_results)