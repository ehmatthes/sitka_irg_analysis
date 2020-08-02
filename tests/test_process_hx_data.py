"""Tests for process_hx_data.py.

Focuses on verifying png and pkl output.

Run this from project root directory:
$ python -m pytest
"""

from os import listdir, path
from pathlib import Path

import pytest

from sitka_irg_analysis import process_hx_data as phd


@pytest.fixture
def run_process_hx_data():
    phd.process_hx_data(root_output_directory='tests/')

def test_png_output_files_exist(run_process_hx_data):
    png_file_path = 'tests/current_ir_plots'
    current_ir_plots_files = [f for f in listdir(png_file_path)
            if path.isfile(path.join(png_file_path, f))]

    png_output_files = [f for f in current_ir_plots_files
            if Path(f).suffix=='.png']

    ref_file_path = 'tests/reference_files'
    reference_files = [f for f in listdir(png_file_path)
            if path.isfile(path.join(png_file_path, f))]
    png_ref_files = [f for f in reference_files
            if Path(f).suffix=='.png']

    # Assert output png file names match reference png file names.
    assert(set(png_output_files) == set(png_ref_files))



