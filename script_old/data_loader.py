# src/data_loader.py

import pandas as pd

def load_data(file_path):
    """
    Function to load data from a CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None
