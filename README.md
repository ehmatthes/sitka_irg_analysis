Indian River Stream Gauge Analysis
===

The [Indian River Stream Gauge](https://water.weather.gov/ahps2/hydrograph.php?wfo=pajk&gage=irva2) measures the height of Indian River just upstream of the bridge on Sawmill Creek Road. Indian River lies in a moderate size drainage, and the river rises quickly during periods of heavy rain and recedes quickly when the intensity of the rain diminishes. The Indian River Stream Gauge may serve as a proxy for measuring factors such as total rainfall, rate of rainfall, ground saturation, and others that are more difficult to measure directly. This analysis examines the possible correlation between the rise of Indian River and the occurrence of landslides along Sitka's road system. In a historical analysis of the period 7/2014 through 9/2019, critical factors were identified that flagged 9 high-risk periods, of which 3 landslides occurred. There were 2 landslides during this period that occurred when the stream gauge did not exceed the critical levels identified in this analysis. The goal of this analysis is to help determine whether the Indian River stream gauge can play a meaningful role in a local landslide warning system. This approach may have relevance to other landslide-prone areas with drainage characteristics similar to Indian River.

Running this code
---

If you want to explore this data on your own, you can set up your own Python environment and run the code yourself.

### Setting up a project environment

- Make sure you have Git and Python 3.6 or later installed on your system.
  - I have been running this on Python 3.8, but I believe it will work on 3.6 or later.
- Choose a location on your system where you want to build this project.
- Clone this repository:

```
~$ git clone https://github.com/ehmatthes/sitka_irg_analysis.git
```

- Open a terminal in the *sitka_irg_analysis* directory, create a Python virtual environment, activate it, and install the required packages:

```
~$ cd sitka_irg_analysis/
sitka_irg_analysis$ python3 -m venv irg_env
sitka_irg_analysis$ source irg_env/bin/activate
(irg_env) sitka_irg_analysis$ pip install -r requirements.txt 
```

### Running the code using existing data

- You can run the code using the current list of known slides, and the current data set. To do this, run the file *process_hx_data.py*:

```
(irg_env) sitka_irg_analysis$ python process_hx_data.py
```

- You should see output about individual plots as they're being generated. A series of new plots should appear in your browser. If your browser doesn't open these plots automatically, look in the *current_ir_plots folder*, and you should find them there.
- When all of the plots have been generated, you should see a summary of the critical events during the historical period analyzed.

### Adding or modifying slide data

- If you want to add or modify slide data, open the file *slide_event.py*. There's a section defining all the known data for each slide. Make a new section for a new slide, or modify the section for an existing slide.
- When you're finished, run *slide_event.py*:

```
(irg_env) sitka_irg_analysis$ python slide_event.py 
```

- You can see the new html summary, docx summary, and JSON summary files in the *known_slides* folder.
- When you run *process_hx_data.py* again, it will use the recently updated information in *known_slides.json*.
  - If you want to run the analysis again against this new slide data, see the section above, "Running the code using existing data".

Questions/ Feedback
---

If you have any questions or feedback, feel free to get in touch:

- email: ehmatthes at gmail
- twitter: [@ehmatthes](https://twitter.com/ehmatthes)