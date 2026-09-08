"""GPU / device detection and configuration for training."""

import tensorflow as tf

from hybrid_ids.config import USE_GPU

_xgb_params_cache = None


def configure_tensorflow():
    """
    Configure TensorFlow devices.

    Note: TensorFlow >= 2.11 does NOT support NVIDIA CUDA on native Windows.
    GPU training for the autoencoder requires WSL2 + CUDA, or runs on CPU here.
    """
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print(f"TensorFlow: using GPU ({len(gpus)} device(s))")
            for gpu in gpus:
                print(f"  - {gpu.name}")
        except RuntimeError as exc:
            print(f"TensorFlow GPU setup warning: {exc}")
        return "gpu"

    if USE_GPU:
        print("TensorFlow: no GPU detected — training autoencoder on CPU.")
        print(
            "  On native Windows, TensorFlow >= 2.11 cannot use NVIDIA CUDA.\n"
            "  Options for GPU autoencoder training:\n"
            "    1. Use WSL2 (Ubuntu) with tensorflow[and-cuda]\n"
            "    2. Continue on CPU (slower but works)"
        )
    else:
        print("TensorFlow: CPU mode (USE_GPU=False in config.py)")
    return "cpu"


def get_xgboost_params():
    """Return XGBoost constructor kwargs for GPU or CPU."""
    global _xgb_params_cache
    if _xgb_params_cache is not None:
        return _xgb_params_cache.copy()

    if not USE_GPU:
        _xgb_params_cache = {"tree_method": "hist", "n_jobs": -1, "device": "cpu"}
        return _xgb_params_cache.copy()

    try:
        import xgboost as xgb
        import numpy as np

        probe = xgb.XGBClassifier(
            n_estimators=1,
            device="cuda",
            tree_method="hist",
        )
        probe.fit(
            np.random.rand(20, 5).astype(np.float32),
            np.random.randint(0, 2, 20),
            verbose=False,
        )
        print("XGBoost: using GPU (CUDA)")
        _xgb_params_cache = {"tree_method": "hist", "device": "cuda", "n_jobs": 1}
    except Exception as exc:
        print(f"XGBoost GPU unavailable ({exc}) — falling back to CPU.")
        _xgb_params_cache = {"tree_method": "hist", "n_jobs": -1, "device": "cpu"}

    return _xgb_params_cache.copy()


def setup_training_devices():
    """Call once at pipeline start."""
    tf_device = configure_tensorflow()
    xgb_params = get_xgboost_params()
    return tf_device, xgb_params
