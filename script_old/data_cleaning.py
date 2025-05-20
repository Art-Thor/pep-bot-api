# src/data_cleaning.py

def clean_data(df):
    """
    Function for data cleaning and preprocessing.
    """
    # Removing empty rows
    df = df.dropna(how='all')
    
    # Filling missing values in important columns
    df['Summary'] = df['Summary'].fillna('')
    df['Assignee'] = df['Assignee'].fillna('Unassigned')
    df['Priority'] = df['Priority'].fillna('Medium')
    
    # Converting text data to lowercase
    df['Summary'] = df['Summary'].str.lower().str.strip()
    df['Assignee'] = df['Assignee'].str.lower().str.strip()
    df['Priority'] = df['Priority'].str.lower().str.strip()
    
    return df
