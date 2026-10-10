"""
experiments/canonical/seed.py
==============================
Deterministic random state and seed manager.
Guarantees multi-library reproducibility across Python, NumPy, TensorFlow,
and Scikit-Learn.
"""

import os
import random
import numpy as np

CANONICAL_SEEDS = [42, 123, 456, 789, 1024]
DEFAULT_SEED = 42

def set_global_seed(seed: int = DEFAULT_SEED) -> None:
    """Set global seeds across all execution frameworks."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
        try:
            tf.config.experimental.enable_op_determinism()
        except Exception:
            pass
    except ImportError:
        pass
        
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

if __name__ == "__main__":
    set_global_seed(42)
    print("✓ Global deterministic seed set to 42.")
