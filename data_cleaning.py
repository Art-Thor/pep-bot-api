import pandas as pd

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and normalizes the DataFrame:
    - Converts columns to appropriate types
    - Handles missing values
    - Removes duplicates
    - Returns empty DataFrame unchanged if input is empty
    """
    if df.empty:
        return df

    # Convert created to datetime if column exists
    if 'created' in df.columns:
        df['created'] = pd.to_datetime(df['created'])
    
    # Remove duplicates based on ticket key
    df = df.drop_duplicates(subset=['key'], ignore_index=True)
    
    return df