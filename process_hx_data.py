"""Process all historical IR gauge data.

This file loads historical data from the Indian River stream gauge. It loads
  values for critical rate of rise, and critical total rise. It then runs
  through all the stream gauge data. It flags any data point at which the 
  stream gauge has met or exceeded these critical values, and captures a
  48-hour period of readings around that point. When these readings are
  plotted, any known slides that occurred during this period are plotted as
  well.

  The script then processes known slide events. If a slide event is not
  already associated with a critical period, 48 hours of readings around that
  slide event are grabbed, and these are plotted as well.

We want to be able to use the output to answer the following questions. In
  this context, 'notification time' refers to the time between the first
  critical point identified in a critical period, and the time at which a
  slide occurred. This is the amount of time people would have to respond
  if a notification were issued the moment the first critical point was
  identified.

  A true positive is a critical point associated with a slide,
  a false positive is a critical point with no associated slide. A false 
  negative is a slide with no associated critical point.

  - How many slides were preceded by a critical point?
  - What do the notification times look like?
  - How many true and false positives and false negatives were there?
  - How many notifications would have been issued over a 5-year period?
  - Was there anything special about slides that were missed? (false negative)
  - Was there anything special about critical points with no slide? (false
      positive)
"""

import pickle

import plot_heights as ph
from slide_event import SlideEvent
import utils.analysis_utils as a_utils
import utils.ir_reading as ir_reading
from utils.analysis_utils import RISE_CRITICAL, M_CRITICAL
from utils.stats import stats


def get_readings_from_data_file(data_file):
    """Process a single data file.
    Returns a list of IRReading objects.
    """
    # Use proper parsing function.
    if 'hx_format' in data_file:
        all_readings = ph.get_readings_hx_format(data_file)
    elif 'arch_format' in data_file:
        all_readings = ph.get_readings_arch_format(data_file)

    return all_readings


def get_reading_sets(readings, known_slides, stats):
    """Takes in a single list of readings, and returns two lists,
    critical_reading_sets and slide_readings_sets.

    critical_reading_sets: lists of readings around critical events, which
      may or may not include a slide
    slide_reading_sets: lists of readings around slide events that are not
      associated with critical points.

    Updates stats.
    """
    # Keep track of earliest and latest reading across all data files.
    #   DEV: This is probably better calculated later, in a separate fn.
    if not stats['earliest_reading']:
        stats['earliest_reading'] = readings[0]
        stats['latest_reading'] = readings[-1]
    else:
        if readings[0].dt_reading < stats['earliest_reading'].dt_reading:
            stats['earliest_reading'] = readings[0]
        if readings[-1].dt_reading > stats['latest_reading'].dt_reading:
            stats['latest_reading'] = readings[-1]

    # Get all the known slides that occurred during these readings.
    slides_in_range = a_utils.get_slides_in_range(
            known_slides, readings)

    # Find the start of all critical periods in this data file.
    first_critical_points = a_utils.get_first_critical_points(readings)
    for reading in first_critical_points:
        print(ir_reading.get_formatted_reading(reading))
    stats['notifications_issued'] += len(first_critical_points)

    # critical_reading_sets is a list of lists. Each list is a set of
    #   readings to plot, based around a first critical point.
    critical_reading_sets = [a_utils.get_48hr_readings(fcp, readings)
                                    for fcp in first_critical_points]

    # Determine which critical sets are associated with slides, so we can
    #   process readings for unassociated slides and build
    #   slide_reading_sets.
    for reading_set in critical_reading_sets:
        critical_points = a_utils.get_critical_points(reading_set)
        relevant_slide = ph.get_relevant_slide(reading_set, known_slides)
        if relevant_slide:
            stats['relevant_slides'].append(relevant_slide)
            stats['associated_notifications'] += 1
            notification_time = ph.get_notification_time(critical_points,
                    relevant_slide)
            stats['notification_times'][relevant_slide] = notification_time
            # Remove this slide from slides_in_range, so we'll
            #   be left with unassociated slides.
            slides_in_range.remove(relevant_slide)
        else:
            # This may be an unassociated notification.
            stats['unassociated_notification_points'].append(
                    critical_points[0])
            stats['unassociated_notifications'] += 1

    # Any slides left in slides_in_range are unassociated.
    #   We can grab a 48-hr data set around these slide.
    slide_reading_sets = []
    for slide in slides_in_range:
        # Get first reading after this slide, and base 48 hrs around that.
        for reading in readings:
            if reading.dt_reading > slide.dt_slide:
                slide_readings = a_utils.get_48hr_readings(
                        reading, readings)
                slide_reading_sets.append(slide_readings)
                break

        stats['unassociated_slides'].append(slide)

    # We aren't processing reading sets separately, so combine them here.
    return critical_reading_sets + slide_reading_sets


def pickle_reading_set(reading_set, root_output_directory=''):
    """Pickle a reading set, for further analysis and quicker plotting."""
    dt_last_reading_str = reading_set[-1].dt_reading.strftime('%m%d%Y')
    dump_filename = f'{root_output_directory}other_output/reading_dump_{dt_last_reading_str}.pkl'
    with open(dump_filename, 'wb') as f:
        pickle.dump(reading_set, f)


def summarize_results(known_slides, stats):
    """Summarize results of analysis."""
    assert(stats['unassociated_notifications']
            == len(stats['unassociated_notification_points']))
    stats['unassociated_slides'] = set(known_slides) - set(stats['relevant_slides'])
    slides_outside_range = []
    for slide in known_slides:
        if ( (slide.dt_slide < stats['earliest_reading'].dt_reading)
                 or (slide.dt_slide > stats['latest_reading'].dt_reading) ):
            stats['unassociated_slides'].remove(slide)
            slides_outside_range.append(slide)
    start_str = stats['earliest_reading'].dt_reading.strftime('%m/%d/%Y')
    end_str = stats['latest_reading'].dt_reading.strftime('%m/%d/%Y')
    print("\n\n --- Final Results ---\n")
    print(f"Data analyzed from: {start_str} to {end_str}")
    print(f"  Critical rise used: {RISE_CRITICAL} feet")
    print(f"  Critical rise rate used: {M_CRITICAL} ft/hr")

    print(f"\nNotifications Issued: {stats['notifications_issued']}")
    print(f"\nTrue Positives: {stats['associated_notifications']}")
    for slide in stats['relevant_slides']:
        print(f"  {slide.name} - Notification time: {stats['notification_times'][slide]} minutes")
    print(f"\nFalse Positives: {stats['unassociated_notifications']}")
    for notification_point in stats['unassociated_notification_points']:
        print(f"  {notification_point.dt_reading.strftime('%m/%d/%Y %H:%M:%S')}")

    print(f"\nFalse Negatives: {len(stats['unassociated_slides'])}")
    for slide in stats['unassociated_slides']:
        print(f"  {slide.name}")
    print(f"\nSlides outside range: {len(slides_outside_range)}")
    for slide in slides_outside_range:
        print(f"  {slide.name}")


def process_hx_data(root_output_directory=''):
    """Process all historical data in ir_data_clean/.

    - Get known slide events.
    - Get readings from file.
    - Pull interesting reading sets from readings. Analysis is done here.
    - Pickle reading sets.
    - Plot reading sets.
    - Summarize results.

    Does not return anything, but generates:
    - pkl files of reading sets.
    - html files containing interactive plots.
    - png files containing static plots.
    - console output summarizing what was found.
    """

    # Get known slides.
    slides_file = 'known_slides/known_slides.json'
    known_slides = SlideEvent.load_slides(slides_file)

    # DEV: Should probably walk the ir_data_clean directory, instead of making
    #      this list manually.
    data_files = [
        'ir_data_clean/irva_utc_072014-022016_hx_format.txt',
        'ir_data_clean/irva_akdt_022016-102019_arch_format.txt',
    ]

    for data_file in data_files:
        readings = get_readings_from_data_file(data_file)
        reading_sets = get_reading_sets(
                readings, known_slides, stats)

        # # Pickle reading sets for faster analysis and plotting later,
        # #   and for use by other programs.
        for reading_set in reading_sets:
            print("Pickling reading sets...")
            pickle_reading_set(reading_set, root_output_directory)

        # # Generate interactive plots.
        for reading_set in reading_sets:
            print("Generating interactive plots...")
            critical_points = a_utils.get_critical_points(reading_set)
            ph.plot_data(
                reading_set,
                known_slides=known_slides,
                critical_points=critical_points,
                root_output_directory=root_output_directory)

        # # Generate static plots.
        for reading_set in reading_sets:
            print("Generating static plots...")
            critical_points = a_utils.get_critical_points(reading_set)
            ph.plot_data_static(
                reading_set,
                known_slides=known_slides,
                critical_points=critical_points,
                root_output_directory=root_output_directory)

    summarize_results(known_slides, stats)


if __name__ == '__main__':
    process_hx_data()