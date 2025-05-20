import matplotlib
matplotlib.use('Agg')  # Must be called before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd
import os
from config import CHART_DIR

def plot_priority_levels(df: pd.DataFrame) -> str:
    """
    Строит круговую диаграмму по приоритетам и сохраняет в CHART_DIR,
    возвращает путь к файлу PNG.
    """
    series = df['priority'].value_counts()
    fig, ax = plt.subplots()
    series.plot.pie(
        autopct='%1.1f%%',
        labels=series.index,
        ax=ax
    )
    ax.set_ylabel('')
    path = os.path.join(CHART_DIR, 'priority_distribution.png')
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path

def plot_alert_types(df: pd.DataFrame, column: str = 'cluster') -> str:
    """
    Строит бар-чарт по указанной колонке (cluster или namespace),
    возвращает путь к PNG.
    """
    series = df[column].value_counts()
    fig, ax = plt.subplots()
    series.plot.bar(ax=ax)
    ax.set_xlabel(column.capitalize())
    ax.set_ylabel('Count')
    path = os.path.join(CHART_DIR, f'{column}_distribution.png')
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path

def plot_cluster_distribution(df: pd.DataFrame) -> str:
    """Строит бар-чарт по кластерам."""
    return plot_alert_types(df, column='cluster')

def plot_namespace_distribution(df: pd.DataFrame) -> str:
    """Строит бар-чарт по неймспейсам."""
    return plot_alert_types(df, column='namespace')

def plot_p1_alerts(df: pd.DataFrame) -> str:
    """
    Строит таблицу P1-такетов как изображение.
    Если P1-такетов нет, создаёт изображение с сообщением.
    """
    p1 = df[df['priority']=='P1'][['key','summary','status','assignee']]
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')
    
    if p1.empty:
        ax.text(0.5, 0.5, 'No P1 alerts', 
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=14)
    else:
        table = ax.table(
            cellText=p1.values,
            colLabels=p1.columns,
            cellLoc='center',
            loc='center'
        )
        # Adjust figure size based on content
        fig.set_figheight(min(0.5 + 0.25 * len(p1), 6))
    
    path = os.path.join(CHART_DIR, 'p1_alerts.png')
    fig.tight_layout()
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path