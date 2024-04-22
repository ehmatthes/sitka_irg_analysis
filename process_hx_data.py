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

import argparse, sys, pickle, pdb

from os import listdir, path
from pathlib import Path

import plot_heights as ph
from slide_event import SlideEvent
import utils.analysis_utils as a_utils
from utils.stats import stats


# Define cli arguments.
parser = argparse.ArgumentParser()
parser.add_argument('--no-interactive-plots',
    help="Do not generate interactive plots.",
    action='store_true')
parser.add_argument('--no-static-plots',
    help="Do not generate static plots.",
    action='store_true')
parser.add_argument('--use-cached-data',
    help="Use pickled data; don't parse raw data files.",
    action='store_true')

args = parser.parse_args()

def process_hx_data(root_output_directory='', data_files=None):
    """Process all historical data in ir_data_clean/.

    - Get known slide events.
    - Get readings from file.
    - Pull interesting reading sets from readings. Analysis is done here.
    - Pickle reading sets.
    - Plot reading sets.
    - Summarize results.

    Accept a data_files arg, so tests can send test data.

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
    if not data_files:
        data_files = [
            'ir_data_clean/irva_utc_072014-022016_hx_format.txt',
            # 'ir_data_clean/irva_akdt_022016-123120_arch_format.txt',
            'ir_data_clean/irva_akdt_022016-033124_arch_format.txt'
            # 'ir_data_other/irva_akdt_123020-033124_arch_format.txt',
        ]

    reading_sets = []

    if not args.use_cached_data:
        print("Parsing raw data files...")
        for data_file in data_files:
            readings = a_utils.get_readings_from_data_file(data_file)
            reading_sets += a_utils.get_reading_sets(readings, known_slides, stats)

    if not args.use_cached_data:
        print("Pickling reading sets...")
        for reading_set in reading_sets:
            # Pickle reading sets for faster analysis and plotting later,
            #   and for use by other programs.
            a_utils.pickle_reading_set(reading_set, root_output_directory)

    if args.use_cached_data:
        print("Reading data from pickled files...")
        pkl_file_path = 'other_output/'
        pkl_files = [f for f in listdir(pkl_file_path)
                if path.isfile(path.join(pkl_file_path, f))
                and Path(f).suffix=='.pkl']
        # pkl_files = [f for f in pkl_files if Path(f).suffix=='.pkl']

        for pkl_file in pkl_files:
            filename = f"{pkl_file_path}{pkl_file}"
            with open(filename, 'rb') as f:
                reading_set = pickle.load(f)
                reading_sets.append(reading_set)

    if not args.no_interactive_plots:
        print("Generating interactive plots...")
        for reading_set in reading_sets:
            critical_points = a_utils.get_critical_points(reading_set)
            ph.plot_data(
                reading_set,
                known_slides=known_slides,
                critical_points=critical_points,
                root_output_directory=root_output_directory)

    if not args.no_static_plots:
        print("Generating static plots...")
        for reading_set in reading_sets:
            critical_points = a_utils.get_critical_points(reading_set)
            ph.plot_data_static(
                reading_set,
                known_slides=known_slides,
                critical_points=critical_points,
                root_output_directory=root_output_directory)

    if not args.use_cached_data:
        a_utils.summarize_results(reading_sets, known_slides, stats)


if __name__ == '__main__':
    # Make sure dir for generated plots exists.
    plots_dir = Path("current_ir_plots")
    if not plots_dir.exists():
        plots_dir.mkdir()
    process_hx_data()