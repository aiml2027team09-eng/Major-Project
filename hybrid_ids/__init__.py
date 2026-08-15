"""
Hybrid Autoencoder + XGBoost Intrusion Detection System.

Stage 1: Autoencoder learns BENIGN network traffic.
Stage 2: Reconstruction error identifies anomalous traffic.
Stage 3: XGBoost classifies anomalous traffic into attack categories.
"""

from hybrid_ids.main import run_pipeline

__all__ = ["run_pipeline"]
