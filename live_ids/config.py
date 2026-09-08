import os



from dataset_config import (

    CAPTURED_DATA_ROOT,

    DEFAULT_DATASET,

    captured_raw_csv,

    get_profile,

    processed_live_folder,

    resolve_model_folder,

)



_profile = get_profile(DEFAULT_DATASET)



ACTIVE_DATASET = _profile.name

FEATURE_SET = _profile.feature_set

DATA_FOLDER = _profile.data_folder

MODEL_FOLDER = resolve_model_folder(_profile)

DEFAULT_CAPTURE_LABEL = _profile.normal_label

ALERT_LOG = _profile.alert_log



CAPTURED_DATA_FOLDER = CAPTURED_DATA_ROOT

CAPTURED_RAW_CSV = captured_raw_csv(_profile)

PROCESSED_LIVE_FOLDER = processed_live_folder(_profile)



# Capture settings

INTERFACE = None

FLOW_IDLE_TIMEOUT = 60

FLOW_FLUSH_INTERVAL = 5

CAPTURE_SAVE_INTERVAL = 10

MAX_ACTIVE_FLOWS = 50000

MIN_PACKETS_PER_FLOW = 2

XGBOOST_MIN_CONFIDENCE = 0.85



os.makedirs(MODEL_FOLDER, exist_ok=True)

os.makedirs(CAPTURED_DATA_FOLDER, exist_ok=True)

os.makedirs(os.path.dirname(CAPTURED_RAW_CSV), exist_ok=True)

os.makedirs(PROCESSED_LIVE_FOLDER, exist_ok=True)

