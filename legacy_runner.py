import shutil
import subprocess
import os
from config import LEGACY_DIR, LEGACY_ART_DIR

def run_legacy():
    """
    Runs the legacy report generation process:
    1. Cleans old artifacts
    2. Dumps Jira data using data_loader.py
    3. Generates legacy visualizations using legacy_report.py
    """
    # 1) Clean old artifacts
    if os.path.exists(LEGACY_DIR):
        shutil.rmtree(LEGACY_DIR)
    os.makedirs(LEGACY_ART_DIR, exist_ok=True)

    # 2) Dump from Jira using old data_loader
    subprocess.run(['python', 'data_loader.py', '--out', f'{LEGACY_DIR}/dump.json'], check=True)

    # 3) Run legacy report generator
    subprocess.run([
        'python', 'legacy_report.py',
        '--dump', f'{LEGACY_DIR}/dump.json',
        '--outdir', LEGACY_ART_DIR
    ], check=True)

    return LEGACY_ART_DIR 