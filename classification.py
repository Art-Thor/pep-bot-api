import pandas as pd
from config import PRIORITY_MAP, EXTRACTION_PATTERNS
import logging

def assign_alert_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 'alert_type' column based on cluster/namespace or summary.
    """
    def _type_for_row(row):
        # If namespace exists
        if row.get('namespace') and row['namespace'] != 'Unknown':
            return f"{row['cluster']},namespace:{row['namespace']}"
        # Otherwise check summary for keywords
        text = row.get('summary','').lower()
        if 'troubleshooting' in text:
            return 'Troubleshooting'
        if 'outage' in text:
            return 'Outage Reporting'
        if 'wiz finding' in text:
            return 'Wiz findings'
        # Can be extended for Snyk/GuardDuty etc.
        # Default - just cluster
        return row.get('cluster','Other') or 'Other'

    df = df.copy()
    df['alert_type'] = df.apply(_type_for_row, axis=1)
    return df

def classify_priorities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classifies ticket priorities using the priority map.
    Returns the DataFrame unchanged if it's empty or missing the priority column.
    """
    if df.empty or 'priority' not in df.columns:
        return df
    # Normalize and map priorities case-insensitively
    norm_priority = df['priority'].astype(str).str.strip().str.title()
    mapped = norm_priority.map(PRIORITY_MAP)
    # Log any unknown priorities
    unknowns = norm_priority[~norm_priority.isin(PRIORITY_MAP.keys())].unique()
    if len(unknowns) > 0:
        logging.warning(f"Unknown priorities encountered: {unknowns}")
    df['priority'] = mapped.fillna(norm_priority)
    return df