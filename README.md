# Major Project — Hybrid Intrusion Detection System

AI-based hybrid model for network intrusion detection using **Autoencoder + XGBoost**. Supports **NSL-KDD** and **CICIDS2018** datasets with separate preprocess, train, and live-monitor paths.

## Project Structure

```
dataset_config.py          # Shared dataset profiles (nsl_kdd | cicids2018)
preprocessing_nsl_kdd.py   # Preprocess NSL-KDD
preprocessing.py           # Preprocess CICIDS2018
hybrid_ids_model.py        # Train autoencoder + XGBoost (--dataset)
live_monitor.py            # Live packet capture + detection (--dataset)
hybrid_ids/                # Training pipeline modules
live_ids/                  # Live capture + inference modules
```

## Setup

```powershell
pip install -r requirements.txt
```

For live capture on Windows, install [Npcap](https://npcap.com/#download) and run PowerShell as **Administrator**.

---

## NSL-KDD Pipeline

```powershell
python preprocessing_nsl_kdd.py
python hybrid_ids_model.py --dataset nsl_kdd
python live_monitor.py --dataset nsl_kdd --interface "Wi-Fi"
```

| Output | Location |
|--------|----------|
| Processed data | `processed_NSL_KDD/` |
| Trained models | `trained_models/nsl_kdd/` (or legacy `trained_models/`) |
| Live alerts | `live_alerts_nsl_kdd.log` |

Live monitoring uses **NSL-KDD connection features** (protocol, service, flag, bytes, host stats).

---

## CICIDS2018 Pipeline

Place `cic.csv` in the project root (or update `CSV_FILE` in `preprocessing.py`).

```powershell
python preprocessing.py
python hybrid_ids_model.py --dataset cicids2018
python live_monitor.py --dataset cicids2018 --interface "Wi-Fi"
```

| Output | Location |
|--------|----------|
| Processed data | `processed_CICIDS2018/` |
| Trained models | `trained_models/cicids2018/` |
| Live alerts | `live_alerts_cicids2018.log` |

Live monitoring uses **68 CICFlowMeter-compatible features**.

---

## Dual live monitoring (both at once)

Train **both** datasets first, then run a single capture that scores every flow with both models:

```powershell
python live_monitor.py --dataset both --interface "Wi-Fi"
```

| Output | Location |
|--------|----------|
| NSL-KDD alerts | `live_alerts_nsl_kdd.log` |
| CICIDS2018 alerts | `live_alerts_cicids2018.log` |

Each flow is analyzed by both pipelines in parallel (one packet capture, two feature extractions, two model inferences).

---

## Capture & Retrain (both datasets)

```powershell
# Capture normal traffic from your network
python live_capture.py --dataset nsl_kdd --interface "Wi-Fi"
python live_capture.py --dataset cicids2018 --interface "Wi-Fi" --label Benign

# Preprocess captured flows
python preprocess_captured.py --dataset nsl_kdd
python preprocess_captured.py --dataset cicids2018 --merge-autoencoder

# Retrain autoencoder on your network's normal traffic
python retrain_autoencoder.py --dataset nsl_kdd
python retrain_autoencoder.py --dataset cicids2018
```

Captured raw CSVs: `captured_data/<dataset>/live_flows_raw.csv`  
Processed live training data: `processed_live/<dataset>/`

---

## Analytics Dashboard

Interactive dashboard for live alerts, model metrics, and expected outcome analysis:

```powershell
pip install streamlit plotly
python run_dashboard.py
```

Opens at **http://localhost:8501** with tabs for:

| Tab | Content |
|-----|---------|
| **Overview** | Alert KPIs, model snapshot, recent alerts |
| **Live Alerts** | Timeline, class distribution, confidence/error charts, export CSV |
| **Model Performance** | Test metrics by stage + confusion matrix images |
| **Expected Outcomes** | Target vs actual pass/fail checklist |
| **Retrain Impact** | Before/after live retrain comparison |

Convert existing text logs to JSONL (optional, for faster loading):

```powershell
python dashboard/convert_logs.py
```

New alerts are written to both `live_alerts_<dataset>.log` and `live_alerts_<dataset>.jsonl`.

---

## Validate When Live Network Has No Attacks

Live traffic is mostly normal — use offline validation plus false-positive checks:

```powershell
python validate_model.py --dataset both
```

This reports:
- **Full test set** — standard accuracy/F1
- **Benign-only** — false positive rate (simulates your normal live network)
- **Attack-only** — detection rate (proves the model catches attacks offline)
- **Live captured normal** — false alarms on your actual network traffic

To improve accuracy on normal-only live traffic, capture and retrain:

```powershell
python live_capture.py --dataset nsl_kdd --interface "Wi-Fi" --duration 180
python retrain_from_live.py --dataset nsl_kdd --skip-capture --threshold-metric accuracy
python validate_model.py --dataset nsl_kdd
```

---

## GPU Training

| Model | Windows (native) | Notes |
|-------|------------------|-------|
| **XGBoost** | GPU (CUDA) | `USE_GPU = True` in `hybrid_ids/config.py` |
| **Autoencoder** | CPU only | TensorFlow ≥ 2.11 has no CUDA on native Windows |

Toggle in `hybrid_ids/config.py`: `USE_GPU = True` or `False`

---

## Default Dataset

The default active dataset is **NSL-KDD**. Override with `--dataset` on any entry-point script, or change `DEFAULT_DATASET` in `dataset_config.py`.

## Important Notes

- Capture only on networks you **own or have permission** to monitor
- NSL-KDD and CICIDS2018 use different feature schemas — always match `--dataset` across preprocess, train, and live monitor
- Large files (`cic.csv`, `processed_*`, `trained_models/`) are gitignored — regenerate locally after cloning

## GitHub

Repository: https://github.com/aiml2027team09-eng/Major-Project
