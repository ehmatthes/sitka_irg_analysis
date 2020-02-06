"""The goal of this program is to generate an ROC curve based on trying
different critical values. I'm not sure how to evaluate the 
'condition negative' value.

For now, this is a tabular summary of the results of varying the critical
values.
"""

import json



if __name__ == '__main__':

    # Get cached results of varying critical values.
    filename = 'other_output/all_results.json'
    with open(filename) as f:
        all_results = json.load(f)

    label_str = "Trial\tR_C\tM_C\tTP\tFP\tFN\tNotification Times"
    print(label_str)
    for trial in all_results:
        # Generate a table of results. Print, and write to file.
        value_str = f"{trial['alpha name']}\t{trial['critical rise']}\t"
        value_str += f"{trial['critical slope']}\t{trial['true positives']}\t"
        value_str += f"{trial['false positives']}\t"
        value_str += f"{trial['false negatives']}\t"
        value_str += f"{sorted(trial['notification times'])}"
        print(value_str)
