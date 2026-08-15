import os

# Paths (reuse hybrid_ids folders)
DATA_FOLDER = "processed_CICIDS2018"
MODEL_FOLDER = "trained_models"
ALERT_LOG = "live_alerts.log"

# Capture settings
# Set to interface name, e.g. "Wi-Fi", "Ethernet", or None to auto-pick first non-loopback
INTERFACE = None

# Close a flow after this many seconds without packets
FLOW_IDLE_TIMEOUT = 60

# How often to flush idle flows (seconds)
FLOW_FLUSH_INTERVAL = 5

# Max flows to keep in memory
MAX_ACTIVE_FLOWS = 50000

# Minimum packets before a flow is analyzed
MIN_PACKETS_PER_FLOW = 2

# Scapy sniff batch size
SNIFF_PACKET_COUNT = 50
