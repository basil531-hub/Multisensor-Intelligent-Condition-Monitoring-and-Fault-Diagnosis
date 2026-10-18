# DrillSense — Sensor-to-Dashboard Predictive Maintenance Pipeline

> A complete, end-to-end condition monitoring pipeline — from raw multi-sensor
> acquisition to machine learning classification to a live health dashboard.
> Built and validated on a vertical drill press, designed to be adapted to
> **any machine** that can be instrumented with current, temperature, and
> vibration sensors.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Arduino](https://img.shields.io/badge/Firmware-Arduino%20Uno-00979D)](https://arduino.cc)
[![XGBoost](https://img.shields.io/badge/Best%20Model-XGBoost%2098.02%25-brightgreen)](ml_pipeline/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## Table of Contents

- [Why This Project Exists](#why-this-project-exists)
- [What's Included](#whats-included)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Case Study: Vertical Drill Press](#case-study-vertical-drill-press)
- [Hardware & Sensors](#hardware--sensors)
- [Signal Conditioning](#signal-conditioning)
- [Quick Start](#quick-start)
- [Dataset](#dataset)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Results (Case Study)](#results-case-study)
- [Dashboard](#dashboard)
- [Adapting This Pipeline to Your Own Machine](#adapting-this-pipeline-to-your-own-machine)
- [Limitations & Future Work](#limitations--future-work)
- [License](#license)

---

## Why This Project Exists

Most predictive maintenance demos are either purely theoretical (a Kaggle
notebook on a synthetic dataset) or purely hardware-focused (a sensor wired
to an Arduino with no analysis pipeline). **DrillSense bridges the gap** —
it's a fully working pipeline covering every stage:

```
Sensors → Microcontroller → Logger → Signal Conditioning →
Phase Detection → Feature Extraction → ML Classification →
Health Score → Dashboard
```

Every stage is implemented, documented, and reusable. The specific machine
used to validate the pipeline is a **vertical drill press**, but nothing
about the architecture is drill-specific:

- The **sensor set** (current, temperature, humidity, vibration) is common
  to almost any motorized machine — pumps, conveyors, fans, lathes, CNC
  spindles, compressors, etc.
- The **signal conditioning** (LPF, moving average, EMA) is generic DSP
  applicable to any noisy analog sensor stream.
- The **phase detection** concept (segmenting a machine's operating cycle
  into states like idle/load/unload) generalizes to any machine with a
  repeating duty cycle.
- The **feature extraction + ML pipeline** operates on generic time-series
  windows and works with any labeled multi-class dataset in the same CSV
  format.
- The **dashboard** is a static HTML file that reads any CSV matching the
  schema — point it at a different machine's data and it works.

If you have a machine, a few cheap sensors, and labeled operating
conditions, you can fork this repo, swap in your data, and have a working
condition monitoring system in an afternoon.

---

## What's Included

- ✅ Arduino firmware for 4-sensor synchronized acquisition at 20 Hz
- ✅ Python live data logger with trial management and real-time plotting
- ✅ Real-time FFT / frequency-domain vibration analysis tool
- ✅ Full ML pipeline: preprocessing, phase detection, sliding-window
  feature extraction (35+ features), 3 dataset variants, 4 classifiers
- ✅ Trial-level train/val/test splitting (no data leakage)
- ✅ Offline inference dashboard with health scoring and maintenance
  recommendations
- ✅ Reference dataset (8 labeled classes, 15 trials each, ~20 Hz) from the
  drill press case study — ready to experiment with out of the box

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          SENSING LAYER                           │
│   Current sensor · Temperature sensor(s) · Vibration sensor      │
│   (ACS712 · LM35 · DHT11 · Piezoelectric — swappable)            │
└──────────────────────────────┬───────────────────────────────────┘
                                 │ Serial @ 115200 baud, 20 Hz CSV
┌──────────────────────────────▼───────────────────────────────────┐
│                  DATA ACQUISITION & LOGGING                      │
│   Arduino Uno firmware  (firmware/main.cpp)                      │
│   Python logger          (data_logger/live_data_logger.py)       │
│   Real-time FFT viewer   (data_logger/real_time_fft_analysis.py) │
│   Output: labeled, trial-organized CSV files                     │
└──────────────────────────────┬───────────────────────────────────┘
                                 │ Labeled CSV dataset
┌──────────────────────────────▼───────────────────────────────────┐
│                     ML PIPELINE (Jupyter)                        │
│   Preprocessing → Phase Detection → Sliding-Window Features      │
│   XGBoost / Random Forest / SVM / Decision Tree                  │
│   Trial-level train/val/test split + GroupKFold CV               │
└──────────────────────────────┬───────────────────────────────────┘
                                 │ Trained model + predictions
┌──────────────────────────────▼───────────────────────────────────┐
│                  INFERENCE DASHBOARD (Offline HTML)              │
│   Health gauge · Sensor time-series · Phase distribution         │
│   Model confidence · Maintenance recommendations                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
drillsense/
├── firmware/
│   ├── main.cpp                      ← Arduino Uno firmware (C++)
│   └── platformio.ini                ← PlatformIO build config
│
├── data_logger/
│   ├── live_data_logger.py           ← Serial reader, trial recorder, live 4-panel plot
│   └── real_time_fft_analysis.py     ← Live FFT / frequency-domain vibration view
│
├── ml_pipeline/
│   └── drill_bit_maintenance.ipynb   ← Full ML pipeline (load → train → evaluate)
│
├── dashboard/
│   └── ml_visualization_dashboard.html  ← Offline inference + visualization dashboard
│
├── data/
│   ├── README.md                     ← Column reference & how to bring your own data
│   └── raw/                          ← Reference dataset (8 labeled CSVs, case study)
│
├── docs/
│   └── images/                       ← Architecture diagrams, dashboard screenshots
│
└── README.md
```

---

## Case Study: Vertical Drill Press

To validate the pipeline end-to-end, it was deployed on a vertical drill
press to classify **drill bit condition** in real time from sensor data
alone — no manual inspection required.

**Eight condition classes** were defined along three axes: bit quality
(good/poor), alignment (aligned/misaligned), and physical state
(normal/flattened/broken). Each class maps to a health score (0–100) and a
maintenance recommendation:

| # | Class | Health Score | Maintenance Action |
|---|-------|:---:|---|
| 1 | good_aligned | 100 | Healthy Operation |
| 2 | good_misaligned | 85 | Inspect Alignment |
| 3 | good_flattened | 70 | Schedule Replacement |
| 4 | poor_aligned | 60 | Monitor Closely |
| 5 | poor_misaligned | 45 | Inspect Alignment (urgent) |
| 6 | good_broken | 30 | Replace Immediately |
| 7 | poor_flattened | 20 | Schedule Replacement (imminent) |
| 8 | poor_broken | 0 | Replace Immediately (critical) |

This class taxonomy, sensor set, and health-score mapping are **specific to
the drill press demo** — see [Adapting This Pipeline](#adapting-this-pipeline-to-your-own-machine)
for how to define your own classes and health scores for a different
machine.

---

## Hardware & Sensors

| # | Component | Spec | Role |
|---|-----------|------|------|
| 1 | ACS712-30A | Hall-effect current sensor, 66 mV/A, ±30 A | Motor load / current draw |
| 2 | LM35 | Analog temp sensor, 10 mV/°C | Localized temperature (e.g. spindle) |
| 3 | DHT11 | Digital temp + humidity, 0–50°C / 20–80% RH | Ambient reference |
| 4 | Piezoelectric (PZT) | Raw analog, broadband | Mechanical vibration |
| 5 | Arduino Uno R3 | ATmega328P, 6 ADC channels | Acquisition microcontroller |

All four sensors are inexpensive, widely available, and easy to source —
this set was chosen specifically so the project is replicable with a
sub-$15 sensor kit. Any of these can be swapped for higher-precision
alternatives (e.g. DS18B20 for temperature, ADXL345 for multi-axis
vibration) without changing the pipeline architecture — just update the
firmware's analog/digital read functions and the CSV column mapping.

---

## Signal Conditioning

| Sensor | Filter | Purpose | Parameters |
|--------|--------|---------|---|
| Current sensor | Hardware RC low-pass filter + firmware RMS averaging | Remove motor switching noise | f_c ≈ 160 Hz; R=1kΩ, C=1µF; N=50 samples |
| Analog temp sensor | Software moving average | Smooth ADC quantization jitter | N = 5–10 samples at 20 Hz |
| Vibration sensor | Hardware LPF + software exponential moving average (EMA) | Remove ultrasonic noise, track vibration trend | LPF f_c ≈ 1 kHz; EMA α = 0.3 |
| Digital temp/humidity sensor | None (internally processed) | — | — |

These conditioning techniques are standard DSP and apply regardless of the
underlying machine — only the cutoff frequencies may need re-tuning for
your specific noise environment.

---

## Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
pip install platformio   # for firmware flashing
```

### 1. Flash the Firmware

```bash
cd firmware/
pio run --target upload --upload-port COM3   # change port as needed
```

Or open `firmware/main.cpp` in the Arduino IDE (requires the **DHT sensor
library** by Adafruit).

### 2. Record Data

```bash
cd data_logger/
python live_data_logger.py --port COM3 --save-dir ../data/raw
```

**Controls:**
- `ENTER` — start / increment a trial
- `ESC` — stop & save CSV, exit

### 2b. (Optional) Live Frequency Analysis

```bash
python real_time_fft_analysis.py --port COM3
```

Streams the vibration channel and displays a live FFT / spectrogram — useful
for identifying characteristic frequencies (e.g. rotational speed harmonics,
bearing fault frequencies) before deciding which features matter for your
machine.

### 3. Run the ML Pipeline

```bash
cd ml_pipeline/
jupyter notebook drill_bit_maintenance.ipynb
```

Set `DATA_DIR` to point at your CSV folder (default: `../data/raw`, which
ships with the reference drill press dataset). The notebook runs the full
pipeline: preprocessing → phase detection → sliding-window feature
extraction (3 dataset variants) → trial-level train/val/test split → train
XGBoost / Random Forest / SVM / Decision Tree → 5-fold GroupKFold
cross-validation → sensor ablation study → export trained model.

### 4. View the Dashboard

Open `dashboard/ml_visualization_dashboard.html` in any modern browser.
Load a session CSV to run inference and view:

- Health score gauge (0–100)
- Sensor time-series (current, vibration, temperature)
- Phase distribution donut chart
- Model confidence bars (all 4 models)
- Maintenance recommendation for the predicted class

---

## Dataset

The reference dataset (`data/raw/`) contains **8 labeled CSV files**, one per
condition class, each with 15 recorded trials at ~20 Hz:

| CSV Filename | Class Label |
|---|---|
| `good_aligned_ok.csv` | good_aligned |
| `good_aligned_flat.csv` | good_flattened |
| `good_aligned_broken.csv` | good_broken |
| `good_misaligned_ok.csv` | good_misaligned |
| `poor_aligned_ok.csv` | poor_aligned |
| `poor_aligned_flat.csv` | poor_flattened |
| `poor_aligned_broken.csv` | poor_broken |
| `poor_misaligned_ok.csv` | poor_misaligned |

**Columns** (see `data/README.md` for full details):

```
Timestamp, Trial_No, Current_A, Power_VA, Temp_1_C, Temp_2_C,
Humidity_%, Vibration, Vib_Strength
```

This dataset is provided **as-is** — it reflects the exact conditions of the
drill press case study (fixed RPM, wooden workpiece, lab environment). It's
useful for:

- Exploring the ML pipeline without collecting your own data first
- Benchmarking alternative models/features against a known baseline
- Understanding the expected CSV schema before wiring up your own machine

To use the pipeline on your own machine, replace the contents of
`data/raw/` with your own CSVs in the same column format (or update the
column-mapping config at the top of the notebook) — see
[Adapting This Pipeline](#adapting-this-pipeline-to-your-own-machine).

---

## Machine Learning Pipeline

### Phase Detection

A physics-based algorithm segments each trial into operational phases based
on adaptive, per-trial statistical thresholds on the current and vibration
signals. For the drill press, six phases were identified:

| Phase | ~Share | Description |
|-------|:------:|-------------|
| Idle | 10% | Motor running, no load |
| Lowering | 12% | Approaching the workpiece |
| Contact | 8% | Initial load spike |
| Active (Drilling) | 55% | Sustained peak load |
| Exit | 8% | Load drop-off |
| Retraction | 7% | Return to idle |

This idle → ramp-up → sustained-load → ramp-down → idle pattern is common to
many cyclic machines (e.g. a press stroke, a pump cycle, a conveyor load
pass) — the thresholding logic is reusable, only the phase *names* are
drill-specific.

### Feature Extraction

Sliding windows (size = 20 samples / 1s, step = 10 samples / 50% overlap)
yield 35–41 features per window across 6 categories:

| Category | Count | Examples |
|---|:---:|---|
| Vibration | 11 | mean, RMS, kurtosis, crest factor, peak-to-peak |
| Current | 7 | mean, RMS, gradient |
| Temperature | 6 | mean, max, rise, sensor differential |
| Humidity | 2 | mean, std |
| Temporal | 5 | elapsed time, progress, phase %, energy integral |
| Cross-sensor fusion | 4 | current×vibration, current×temperature, etc. |
| Phase proportions (Dataset C only) | 6 | fraction of window in each phase |

### Dataset Variants & Classifiers

| Variant | Description |
|---|---|
| A | All phases, standard 35 features |
| B | Only "active load" phases, same 35 features |
| C | All phases + 6 phase-proportion features (41 total) |

Four classifiers trained per variant: **XGBoost**, **Random Forest**, **SVM
(RBF)**, **Decision Tree**. Splitting is done at the **trial level** (70/15/15
train/val/test) to avoid leakage between correlated windows, with
**GroupKFold cross-validation**.

---

## Results (Case Study)

| Model | Dataset | Test Acc | F1 |
|-------|---------|:--------:|:--:|
| **XGBoost** | **C** | **98.02%** | **97.99%** |
| XGBoost | A | 97.31% | 97.28% |
| Random Forest | C | 94.03% | 95.71% |
| SVM (RBF) | A | 91.83% | 91.76% |
| Decision Tree | A | 88.20% | 88.08% |

- **Best model**: XGBoost on Dataset C — 98.02% test accuracy, 97.4%
  majority-vote confidence
- **Sensor ranking** (ablation study): Vibration > Current > Temperature >
  Humidity
- **Held-out test**: model correctly classified an unlabeled session CSV
  with 0.983 confidence, confirming the model generalizes beyond the
  training trials

---

## Dashboard

The dashboard (`dashboard/ml_visualization_dashboard.html`) is a single,
dependency-free HTML file. Load any session CSV and it runs the full
pipeline — preprocessing, phase detection, sliding-window feature
extraction, and majority-vote inference — entirely client-side, then
displays:

- Health score gauge (0–100, color-coded)
- KPI cards: predicted class, model accuracy, confidence
- Sensor snapshot tiles (current, vibration, temperature, humidity)
- Multi-line sensor time-series chart
- Phase distribution donut chart
- Model confidence bars for all 4 trained models
- Static model performance comparison table
- Sensor contribution (ablation) chart
- Condition sidebar with health scores, predicted class highlighted

> The "Live Monitoring" label refers to the dashboard's animated visual
> style — it's an **offline** tool that processes a saved session CSV, not a
> live sensor connection. Adding a live serial-to-dashboard bridge is a
> natural next step (see [Future Work](#limitations--future-work)).

![Dashboard Screenshot](docs/images/dashboard.png)

---

## Adapting This Pipeline to Your Own Machine

This is the core value of the repo — here's the checklist to retarget it:

1. **Define your condition classes.** Replace the 8 drill bit classes with
   whatever states matter for your machine (e.g. `normal`, `bearing_wear`,
   `belt_slip`, `overload`). Update `HEALTH_SCORES` in the notebook config.

2. **Wire up sensors.** Keep the same CSV schema (`Timestamp, Trial_No,
   Current_A, ..., Vibration, Vib_Strength`) or update the column names in
   `firmware/main.cpp`, `data_logger/live_data_logger.py`, and the notebook's
   data-loading cell consistently.

3. **Collect labeled trials.** Run your machine in each known condition,
   recording multiple trials per class (more trials = better trial-level
   splitting). The logger's trial-based recording (`ENTER`/`ESC`) works
   as-is.

4. **Re-tune signal conditioning.** Adjust filter cutoffs / window sizes
   based on your machine's actual dynamics — use
   `real_time_fft_analysis.py` to inspect your vibration signal's frequency
   content first.

5. **Re-derive phase detection thresholds.** If your machine has a cyclic
   duty cycle (load/unload, on/off, etc.), adapt the phase rules in section
   6.2 of the notebook. If your machine runs continuously without phases,
   you can skip phase detection and use Dataset A (no phase-proportion
   features).

6. **Re-run the notebook.** The feature extraction, splitting, training, and
   evaluation code is generic — it operates on whatever classes and CSV
   columns you've configured.

7. **Point the dashboard at your session CSVs.** No code changes needed if
   the column schema matches.

---

## Limitations & Future Work

**Current limitations:**
- Validated on a single machine/substrate configuration; generalization to
  other operating conditions requires retraining
- Fixed operating speed during data collection
- Inference runs on a connected PC, not embedded hardware


**Planned / suggested extensions:**
- Multi-speed / multi-substrate data collection for a more general model
- Multi-axis accelerometer + frequency-domain (FFT/PSD) features
- Edge deployment (Raspberry Pi / Jetson) for standalone inference
- Live serial-to-dashboard bridge for true real-time monitoring
- Online/incremental learning for adapting to gradual wear without full
  retraining

Contributions and forks for other machine types are welcome. If you adapt this pipeline to a different system, feel free to share it as a case study.

If you find this project useful, please consider giving it a ⭐ on GitHub.


---

## License

MIT License — see [LICENSE](LICENSE) for details.
```
