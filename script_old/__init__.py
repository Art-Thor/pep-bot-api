# src/__init__.py

"""
Initialization of the src package.

This file allows importing modules of the src package directly,
which simplifies access to the project's functions.
"""

from .data_loader import load_data
from .data_cleaning import clean_data
from .classification import classify_alerts, define_priority
from .visualization import plot_alert_types, plot_priority_levels
from .utils import *

