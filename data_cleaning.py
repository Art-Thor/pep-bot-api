import pandas as pd

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Приводит колонки к нужным типам, обрабатывает пропуски, 
    дропает дубликаты и т.п.
    """
    # пример: приводим created в datetime
    df['created'] = pd.to_datetime(df['created'])
    # убираем дубликаты
    df = df.drop_duplicates(subset=['key'])
    # можно добавить любое другое предобработку
    return df