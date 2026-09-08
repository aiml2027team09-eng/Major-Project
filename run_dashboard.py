#!/usr/bin/env python
"""Launch the Hybrid IDS Streamlit dashboard."""

import subprocess
import sys
from pathlib import Path


def main():
    app_path = Path(__file__).resolve().parent / "dashboard" / "app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.headless", "true"],
        check=True,
    )


if __name__ == "__main__":
    main()
