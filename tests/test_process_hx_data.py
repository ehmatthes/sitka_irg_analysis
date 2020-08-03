"""Tests for process_hx_data.py.

Focuses on verifying png and pkl output.

Run this from project root directory:
$ python -m pytest
"""

from os import listdir, path
from pathlib import Path
import os, shutil, filecmp

import pytest

from sitka_irg_analysis import process_hx_data as phd


@pytest.fixture(scope="session")
def run_process_hx_data():
    # Clear any previous output.
    shutil.rmtree('tests/current_ir_plots')
    shutil.rmtree('tests/other_output')
    os.mkdir('tests/current_ir_plots')
    os.mkdir('tests/other_output')

    phd.process_hx_data(root_output_directory='tests/')


def get_current_ir_plots_files():
    current_ir_plots_file_path = 'tests/current_ir_plots'
    return [f for f in listdir(current_ir_plots_file_path)
            if path.isfile(path.join(current_ir_plots_file_path, f))]

def get_png_output_files():
    return [f for f in get_current_ir_plots_files()
            if Path(f).suffix=='.png']

def get_reference_files():
    ref_file_path = 'tests/reference_files'
    return [f for f in listdir(ref_file_path)
            if path.isfile(path.join(ref_file_path, f))]

def get_png_reference_files():
    return [f for f in get_reference_files() if Path(f).suffix=='.png']


def test_png_output_files_exist(run_process_hx_data):
    # Assert output png file names match reference png file names.
    png_output_files = get_png_output_files()
    png_ref_files = get_png_reference_files()
    assert(set(png_output_files) == set(png_ref_files))

def test_png_output_files_contents(run_process_hx_data):
    # Assert content of png files match reference files.
    png_output_files = get_png_output_files()
    png_ref_files = get_png_reference_files()
    for output_file, ref_file in zip(png_output_files, png_ref_files):
        output_file = f"tests/current_ir_plots/{output_file}"
        ref_file = f"tests/reference_files/{ref_file}"
        assert(filecmp.cmp(output_file, ref_file, shallow=False))