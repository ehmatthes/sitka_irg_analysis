"""Utility functions for analyzing stream gauge data, and slide data.
"""

import math, datetime, pickle

from xml.etree import ElementTree as ET

import requests, pytz

# Assume this file will be imported in a directory outside of utils.
import utils.ir_reading as ir_reading
import plot_heights as ph


# Critical values.
# Critical rise in feet. Critical slope, in ft/hr.
RISE_CRITICAL = 2.5
M_CRITICAL = 0.5
RIVER_MIN_HEIGHT = 20.5


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
    root = ET.fromstring(data)
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

        reading = ir_reading.IRReading(dt_reading_utc, height)
        readings.append(reading)

    # Readings need to be in chronological order.
    # DEV: This should be an absolute ordering, not just relying on 
    #      input file format.
    readings.reverse()

    print(f"    Found {len(readings)} readings.")
    return readings


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
    slides_in_range = get_slides_in_range(
            known_slides, readings)

    # Find the start of all critical periods in this data file.
    first_critical_points = get_first_critical_points(readings)
    for reading in first_critical_points:
        print(ir_reading.get_formatted_reading(reading))
    stats['notifications_issued'] += len(first_critical_points)

    # critical_reading_sets is a list of lists. Each list is a set of
    #   readings to plot, based around a first critical point.
    critical_reading_sets = [get_48hr_readings(fcp, readings)
                                    for fcp in first_critical_points]

    # Determine which critical sets are associated with slides, so we can
    #   process readings for unassociated slides and build
    #   slide_reading_sets.
    for reading_set in critical_reading_sets:
        critical_points = get_critical_points(reading_set)
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
                slide_readings = get_48hr_readings(
                        reading, readings)
                slide_reading_sets.append(slide_readings)
                break

        stats['unassociated_slides'].append(slide)

    return critical_reading_sets + slide_reading_sets


def pickle_reading_set(reading_set, root_output_directory=''):
    """Pickle a reading set, for further analysis and quicker plotting."""
    dt_last_reading_str = reading_set[-1].dt_reading.strftime('%m%d%Y')
    dump_filename = f'{root_output_directory}other_output/reading_dump_{dt_last_reading_str}.pkl'
    with open(dump_filename, 'wb') as f:
        pickle.dump(reading_set, f)


def get_critical_points(readings):
    """Return critical points.
    A critical point is the first point where the slope has been critical
    over a minimum rise. Once a point is considered critical, there are no
    more critical points for the next 6 hours.
    """
    print("  Looking for critical points...")

    # What's the longest it could take to reach critical?
    #   RISE_CRITICAL / M_CRITICAL
    #  If it rises faster than that, we want to know.
    #    Multiplied by 4, because there are 4 readings/hr.
    readings_per_hr = get_reading_rate(readings)
    max_lookback = math.ceil(RISE_CRITICAL / M_CRITICAL) * readings_per_hr

    critical_points = []
    # Start with 10th reading, so can look back.
    for reading_index, reading in enumerate(readings[max_lookback:]):
        # print(f"  Examining reading: {reading.get_formatted_reading()}")

        # If reading is below the base level of the river plus the minimum
        #   critical rise, this reading can't be critical, and we don't need
        #   to examine it.
        if reading.height < RIVER_MIN_HEIGHT + RISE_CRITICAL:
            continue

        # Get prev max_lookback readings.
        prev_readings = [reading for reading in readings[reading_index-max_lookback:reading_index]]
        for prev_reading in prev_readings:
            rise = ir_reading.get_rise(reading, prev_reading)
            m = ir_reading.get_slope(reading, prev_reading)
            # print(f"    Rise: {rise} Slope: {m}")
            if rise >= RISE_CRITICAL and m > M_CRITICAL:
                # print(f"Critical point: {reading.get_formatted_reading()}")
                critical_points.append(reading)
                break

    print(f"    Found {len(critical_points)} critical points.")
    return critical_points


def get_reading_rate(readings):
    """Return readings/hr.
    Should be 1 or 4, for hourly or 15-min readings.
    """
    reading_interval = (
        (readings[1].dt_reading - readings[0].dt_reading).total_seconds() // 60)
    reading_rate = int(60 / reading_interval)
    # print(f"Reading rate for this set of readings: {reading_rate}")

    return reading_rate


def get_recent_readings(readings, hours_lookback):
    """From a set of readings, return only the most recent x hours
    of readings.
    """
    print(f"  Getting most recent {hours_lookback} hours of readings...")
    last_reading = readings[-1]
    td_lookback = datetime.timedelta(hours=hours_lookback)
    dt_first_reading = last_reading.dt_reading - td_lookback
    recent_readings = [r for r in readings
                            if r.dt_reading >= dt_first_reading]

    print(f"    Found {len(recent_readings)} recent readings.")
    return recent_readings


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
            rise = ir_reading.get_rise(reading, prev_reading)
            m = ir_reading.get_slope(reading, prev_reading)
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


def get_48hr_readings(first_critical_point, all_readings):
    """Return 24 hrs of readings before, and 24 hrs of readings after the
    first critical point."""
    readings_per_hr = get_reading_rate(all_readings)
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

def get_earliest_latest_readings(reading_sets,stats):
    """Find the earliest and latest readings in a set."""
    earliest = reading_sets[0][0]
    latest = reading_sets[-1][-1]

    for reading_set in reading_sets:
        for reading in reading_set:
            if reading.dt_reading < earliest.dt_reading:
                earliest = reading
            elif reading.dt_reading > latest.dt_reading:
                # A reading can't be earliest and latest, so elif should work.
                latest = reading

    stats['earliest_reading'] = earliest
    stats['latest_reading'] = latest


def summarize_results(reading_sets, known_slides, stats):
    """Summarize results of analysis."""
    get_earliest_latest_readings(reading_sets, stats)

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