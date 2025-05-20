import pandas as pd
from config import PRIORITY_MAP

def classify_priorities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Нормализует приоритеты в столбце 'priority' в категории P1–P4/Unknown.
    """
    df['priority'] = df['priority'].map(PRIORITY_MAP).fillna('Unknown')
    return df