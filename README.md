# Major Project — Hybrid Intrusion Detection System

AI-based hybrid model for network intrusion detection using **Autoencoder + XGBoost** on the CICIDS2018 dataset.

## Project Structure

```
preprocessing.py       # Preprocess raw CICIDS2018 CSV
hybrid_ids_model.py    # Train autoencoder + XGBoost
live_monitor.py        # Live packet capture + anomaly detection
hybrid_ids/            # Training pipeline modules
live_ids/              # Live capture + inference modules
```

## Setup

### 1. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 2. Live capture only — install Npcap (Windows)

1. Download [Npcap](https://npcap.com/#download)
2. Install with **"Install Npcap in WinPcap API-compatible Mode"** enabled
3. Or run the setup script:

```powershell
.\install_live_ids.ps1
```

## Train Models (offline)

1. Place `cic.csv` in the project root
2. Update the CSV path in `preprocessing.py` if needed
3. Run:

```powershell
python preprocessing.py
python hybrid_ids_model.py
```

This creates `processed_CICIDS2018/` and `trained_models/`.

## Live Packet Monitoring

**Run PowerShell as Administrator** (required for packet capture).

```powershell
# List network interfaces
python live_monitor.py --list-interfaces

# Start live monitoring
python live_monitor.py --interface "Wi-Fi"
python live_monitor.py --interface "Ethernet"
```

### What happens live

1. **Scapy** captures packets from your network interface
2. Packets are grouped into **flows** (TCP/UDP/ICMP)
3. **68 CICIDS-compatible features** are extracted per flow
4. Saved **preprocessor** scales features
5. **Autoencoder** flags anomalies (reconstruction error > threshold)
6. **XGBoost** classifies flagged flows into attack types
7. Alerts are printed and saved to `live_alerts.log`

### Configuration

Edit `live_ids/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `INTERFACE` | `None` | Auto-pick interface, or set e.g. `"Wi-Fi"` |
| `FLOW_IDLE_TIMEOUT` | `60` | Seconds before a flow is finalized |
| `MIN_PACKETS_PER_FLOW` | `2` | Minimum packets to analyze a flow |

## Important Notes

- Capture only on networks you **own or have permission** to monitor
- Live features are approximations of CICFlowMeter — retrain on your network's normal traffic for best results
- For production, consider using [CICFlowMeter](https://github.com/ahlashkari/CICFlowMeter) for exact feature parity

## GitHub

Repository: https://github.com/aiml2027team09-eng/Major-Project

Large files (`cic.csv`, `processed_CICIDS2018/`, `trained_models/`) are gitignored. Regenerate locally after cloning.
