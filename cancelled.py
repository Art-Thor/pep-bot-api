from typing import List

# из config
from config import CANCELLED_KEYWORDS

def detect_cancelled(df) -> df:
    """
    Добавляет булев столбец 'cancelled', если в summary или статусе 
    найдены ключевые слова.
    """
    lower = df['summary'].str.lower()
    status_lower = df['status'].str.lower()
    mask = lower.apply(lambda s: any(kw in s for kw in CANCELLED_KEYWORDS)) \
        | status_lower.apply(lambda s: any(kw in s for kw in CANCELLED_KEYWORDS))
    df['cancelled'] = mask
    return df