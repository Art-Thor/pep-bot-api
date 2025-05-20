import pandas as pd
from config import PRIORITY_MAP

def classify_priorities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classifies ticket priorities using the priority map.
    Returns the DataFrame unchanged if it's empty or missing the priority column.
    """
    if df.empty or 'priority' not in df.columns:
        return df
    df['priority'] = df['priority'].map(PRIORITY_MAP).fillna('Unknown')
    return df