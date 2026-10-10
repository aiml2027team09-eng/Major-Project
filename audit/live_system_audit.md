# Live System Audit Report
**Project:** Hybrid Intrusion Detection System (`hybrid_ids`)  
**Auditor:** Research-Grade NIDS Audit Team  
**Date:** 2026-10-10  
**Scope:** Live packet sniffing, flow reconstruction, feature fidelity, and operational false alarm rates  

---

## 1. Live Sniffing Architecture & Flow Tracking

- **Capture Backend**: Scapy sniffing over Npcap physical and loopback drivers.
- **Flow Reconstruction (`live_ids/flow_tracker.py`)**:
  - Key tuple: `(src_ip, dst_ip, src_port, dst_port, proto)` canonicalized bidirectionally.
  - Aggregation: Packet lengths, timestamps, TCP flags, header lengths, window sizes.
  - Flow Termination: Handled via `FLOW_IDLE_TIMEOUT` (recently lowered from 60s to 5s).

---

## 2. The 100% False Alarm Rate Phenomenon on CICIDS2018

### 2.1 The Phenomenon
In validation reports:
```text
[4] LIVE CAPTURED NORMAL TRAFFIC (CICIDS2018)
    False positive rate: 1.0000 (23/23 false alarms)
```
Every single benign flow captured on the live interface was flagged as an anomaly by the Autoencoder ($L_2$ error $> \tau$).

### 2.2 Root Cause Analysis
1. **Feature Semantics Discrepancy**:
   - CICIDS2018 benchmark features were generated using Java-based **CICFlowMeter v3/v4**.
   - CICFlowMeter calculates statistical quantities such as `Flow IAT Mean`, `Flow IAT Std`, `Active Mean`, `Idle Mean`, and `Init_Win_bytes_forward` using specific internal timer resolutions (microseconds).
   - Scapy in Python computes timestamps via `time.time()`, and the simplified feature builder approximate active/idle states with different definitions.
2. **Missing Feature Zero-Filling**:
   - Multiple CICFlowMeter features (e.g. `Fwd Avg Bytes/Bulk`, sub-flow counters) cannot be measured over short live capture sessions and default to 0.0, placing the flow outside the trained benign manifold.
3. **Distribution Shift**:
   - Real-world Wi-Fi traffic involves modern TLS 1.3 / QUIC UDP packets on port 443 with large packet sizes and different TCP window scaling than the 2018 simulated testbed network.

---

## 3. Required Action Items

1. Create `metadata/live_feature_compatibility.csv` documenting every feature's equivalence rating (`EXACT`, `APPROXIMATE`, `UNAVAILABLE`).
2. Establish a `trusted_baseline/` calibration period where the Autoencoder calibrates its threshold on confirmed benign flows captured from the local network environment.
3. Document live operational latency, packet queue depth, and throughput without making unsubstantiated "real-time" claims.
