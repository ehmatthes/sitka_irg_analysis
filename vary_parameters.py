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

# Intervals over which to iterate 