"""The goal of this program is to generate an ROC curve based on trying
different critical values. I'm not sure how to evaluate the 
'condition negative' value.

For now, this is a tabular summary of the results of varying the critical
values.
"""

import json

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def generate_plot(all_results):
    """For now, generate a simple TP vs FP and TP vs FN plot.
    """

    # Generate data and labels.
    x_values = [trial['false positives'] for trial in all_results]
    y_values = [trial['true positives'] for trial in all_results]
    labels = [trial['alpha name'] for trial in all_results]
    # Labels overlap, so need to build series of labels and leave some blank.
    # Build a dict of labels, and if coordinates already in, add to that label.
    # Keys are point tuples, values are labels.
    label_dict = {}
    for x, y, label in zip(x_values, y_values, labels):
        try:
            label_dict[(x, y)] += label
        except KeyError:
            label_dict[(x, y)] = label

    fig, ax = plt.subplots()
    ax.scatter(x_values, y_values)

    ax.set_title('True Postives vs False Positives')
    ax.set_xlabel('False Positives')
    ax.set_ylabel('True Positives')

    # Add labels.
    for point, label in label_dict.items():
        ax.text(point[0], point[1], label)

    # Make integer tick marks.
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))

    plt.show()

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

    generate_plot(all_results)