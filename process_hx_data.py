"""Process all historical IR gauge data.
How many slides have were preceded by a critical point?
What do the notification times look like?
How many false positives were there?
How many notifications would have been issued over a 5-year period?
How many slides were not preceded by a critical point?
Was there anything special about those slides?
What did the river data look like for those slides?
"""

import pickle

import plot_heights as ph
from slide_event import SlideEvent
import utils.analysis_utils as a_utils
from utils.analysis_utils import RISE_CRITICAL, M_CRITICAL


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
        slides_in_range = a_utils.get_slides_in_range(
                known_slides, all_readings)

        # Find the start of all critical periods in this data file.
        first_critical_points = a_utils.get_first_critical_points(all_readings)
        for reading in first_critical_points:
            print(reading.get_formatted_reading())
        notifications_issued += len(first_critical_points)

        # reading_sets is a list of lists. Each list is a set of readings to plot,
        #   based around a first critical point.
        reading_sets = [a_utils.get_48hr_readings(fcp, all_readings)
                                        for fcp in first_critical_points]

        for reading_set in reading_sets:
            # Dump these readings to a file, so I can analyze them separately
            #   when helpful to do so.
            dt_last_reading_str = reading_set[-1].dt_reading.strftime('%m%d%Y')
            dump_filename = f'other_output/reading_dump_{dt_last_reading_str}.pkl'
            with open(dump_filename, 'wb') as f:
                pickle.dump(reading_set, f)

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
                    slide_readings = a_utils.get_48hr_readings(
                            reading, all_readings)
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

