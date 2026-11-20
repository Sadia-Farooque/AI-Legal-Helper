"""
Convenience launcher for the Streamlit application.
Usage:
    python run_app.py
"""

import os
import subprocess
import sys

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(root, "app", "Home.py")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        app_path,
        "--browser.gatherUsageStats=false"
    ]

    print(f"[AI-Legal-Helper] Launching Streamlit from: {app_path}")
    print(f"[AI-Legal-Helper] Command: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
