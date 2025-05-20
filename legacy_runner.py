import shutil
import subprocess
import os
import sys
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

    # Get the directory containing this script and the script_old directory
    base = os.path.dirname(__file__)
    script_old_dir = os.path.join(base, 'script_old')

    # 2) Dump from Jira using old data_loader
    loader = os.path.join(script_old_dir, 'data_loader.py')
    if not os.path.exists(loader):
        raise FileNotFoundError(f"Legacy data loader not found: {loader}")
    
    subprocess.run([
        sys.executable,
        loader,
        '--out', os.path.join(LEGACY_DIR, 'dump.json')
    ], check=True)

    # 3) Run legacy report generator
    report = os.path.join(script_old_dir, 'main.py')  # Using main.py as the report generator
    if not os.path.exists(report):
        raise FileNotFoundError(f"Legacy report generator not found: {report}")
    
    subprocess.run([
        sys.executable,
        report,
        '--dump', os.path.join(LEGACY_DIR, 'dump.json'),
        '--outdir', LEGACY_ART_DIR
    ], check=True)

    return LEGACY_ART_DIR 