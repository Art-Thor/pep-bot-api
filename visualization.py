import matplotlib
matplotlib.use('Agg')  # Must be called before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd
import os
from config import CHART_DIR

def plot_priority_levels(df: pd.DataFrame) -> str:
    """
    Creates a pie chart for priorities and saves it to CHART_DIR,
    returns the path to the PNG file.
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
    Creates a bar chart for the specified column (cluster or namespace),
    returns the path to the PNG file.
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
    """Creates a bar chart for clusters."""
    return plot_alert_types(df, column='cluster')

def plot_namespace_distribution(df: pd.DataFrame) -> str:
    """Creates a bar chart for namespaces."""
    return plot_alert_types(df, column='namespace')

def plot_ticket_table(df: pd.DataFrame, priority: str = None, status: str = None, filename: str = 'tickets.png') -> str:
    """
    Creates a table of tickets filtered by priority or status as an image.
    If there are no matching tickets, creates an image with a message.
    """
    if priority:
        filtered = df[df['priority'] == priority][['key', 'summary', 'status', 'assignee']]
        label = priority
    elif status:
        filtered = df[df['status'].str.lower() == status.lower()][['key', 'summary', 'status', 'assignee']]
        label = status.capitalize()
    else:
        filtered = df[['key', 'summary', 'status', 'assignee']]
        label = 'Tickets'

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')

    if filtered.empty:
        ax.text(0.5, 0.5, f'No {label} tickets',
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=14)
    else:
        table = ax.table(
            cellText=filtered.values,
            colLabels=filtered.columns,
            cellLoc='center',
            loc='center'
        )
        # Adjust figure size based on content
        fig.set_figheight(min(0.5 + 0.25 * len(filtered), 6))

    path = os.path.join(CHART_DIR, filename)
    fig.tight_layout()
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path

def plot_priority_changes(priority_history: dict) -> str:
    """
    Creates a visualization of priority changes over time for tickets.
    Returns the path to the saved image.
    """
    # Convert history to DataFrame
    records = []
    for ticket_key, changes in priority_history.items():
        for change in changes:
            records.append({
                'ticket': ticket_key,
                'priority': change['priority'],
                'timestamp': change['timestamp']
            })
    
    if not records:
        # Create empty plot with message
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.axis('off')
        ax.text(0.5, 0.5, 'No priority changes recorded', 
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=14)
    else:
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot each ticket's priority changes
        for ticket in df['ticket'].unique():
            ticket_data = df[df['ticket'] == ticket]
            ax.plot(ticket_data['timestamp'], ticket_data['priority'], 
                   marker='o', label=ticket, linestyle='-')
        
        # Customize plot
        ax.set_title('Ticket Priority Changes Over Time')
        ax.set_xlabel('Time')
        ax.set_ylabel('Priority')
        plt.xticks(rotation=45)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
    
    # Save the plot
    path = os.path.join(CHART_DIR, 'priority_changes.png')
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path

# Backward compatibility for P1 alerts
def plot_p1_alerts(df: pd.DataFrame) -> str:
    return plot_ticket_table(df, priority='P1', filename='p1_alerts.png')