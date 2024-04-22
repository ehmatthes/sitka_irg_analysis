Clean data files
---

These are the files used to complete the IR gauge analysis.
They are taken from larger files, and together they represent the most
  complete data set I have been able to put together.
They are a mix of several different formats.

Each file in here has, within it, a consistent reading interval.

irva_utc_072014-022016_hx_format.txt
- probably utc?
- hourly readings
- akdt time started 02:00 3/9/14; ended 02:00 11/2/14
  - if UTC, shouldn't see any change 02:00 11/2/14
  - no change then

irva_akdt_022016-033124_arch_format.txt
- akdt and akst
- 15min readings
- akdt started 02:00 3/13/16; ended 02:00 11/6/16
  - should see skip ahead to 03:00 on 3/13
    - yes, skips ahead to 03:00; no 02:00
  - should see fall back to 01:00 11/6
- This file was updated on 4/22/24, to include data through 03/31/2024.
  - See: https://github.com/ehmatthes/sitka_irg_analysis/issues/31