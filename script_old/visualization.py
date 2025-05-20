# src/visualization.py

import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
import matplotlib.pyplot as plt

def plot_cancellation_reasons(input_file):
    """
    Generate a bar chart from a text file with cancellation reasons.
    """
    # Load the cancellation reasons from the text file
    try:
        df = pd.read_csv(input_file, sep='\t', engine='python')
    except FileNotFoundError:
        print(f"File {input_file} not found.")
        return

    if df.empty or 'Reason' not in df.columns:
        print("The cancellation reasons file is empty or not properly formatted.")
        return

    # Count reasons
    reason_counts = df['Reason'].value_counts()

    if reason_counts.empty:
        print("No reasons provided in the cancellation file.")
        return

    # Plot the bar chart
    plt.figure(figsize=(10, 6))
    reason_counts.plot(kind='bar', color='#3498DB', edgecolor='black')
    plt.title('Cancellation Reasons Analytics')
    plt.xlabel('Reason')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save the plot
    figures_dir = create_figures_dir()
    output_file = os.path.join(figures_dir, 'cancellation_reasons.png')
    plt.savefig(output_file)
    plt.close()
    print(f"Cancellation reasons analytics saved to {output_file}.")

# Define color mapping for priority levels
priority_colors = {
    'P1': '#E74C3C',       # Red
    'P2': '#E67E22',       # Orange
    'P3': '#F1C40F',       # Yellow
    'Cancelled': '#3498DB',# Blue
    'Other': '#95A5A6'     # Grey
}

# User-side request types
user_request_types = [
    "Team Change Request",
    "Change Request",
    "Password Reset Request",
    "User Provisioning Request"
]

def create_figures_dir():
    """
    Utility function to ensure the figures directory exists.
    """
    figures_dir = '../reports/figures/'
    if not os.path.exists(figures_dir):
        os.makedirs(figures_dir)
    return figures_dir

def plot_priority_pie(df):
    """
    Function to create a pie chart of alert distribution by priority levels.
    """
    priority_counts = df['Priority Level'].value_counts()
    priority_labels = priority_counts.index

    # Get colors for the priorities
    colors = [priority_colors.get(label, '#95A5A6') for label in priority_labels]

    fig = plt.figure(figsize=(8, 8))
    plt.pie(priority_counts, labels=priority_labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Alert Distribution by Priority Levels')
    plt.axis('equal')  # Make the pie chart circular
    plt.tight_layout()

    return fig

def plot_alert_types(df):
    """
    Function to visualize the number of alerts by types.
    """
    plt.figure(figsize=(10, 6))
    sns.countplot(y='Alert Type', data=df, order=df['Alert Type'].value_counts().index)
    plt.title('Number of Alerts by Types')
    plt.xlabel('Count')
    plt.ylabel('Alert Type')
    plt.tight_layout()

    # Save the plot
    figures_dir = create_figures_dir()
    plt.savefig(os.path.join(figures_dir, 'alert_types.png'))
    plt.close()

def plot_alert_types_with_priority(df):
    """
    Function to create a bar chart of alerts by types with a breakdown by priorities.
    Excludes user-side requests from the visualization.
    """
    # Exclude user-side requests
    df_filtered = df[~df['Alert Type'].isin(user_request_types)]

    return _plot_alerts_by_priority(
        df_filtered,
        'alert_types_with_priority.png',
        "Number of Alerts by Types and Priorities"
    )

def plot_user_requests_by_priority(df):
    """
    Function to create a bar chart for user-side requests with a breakdown by priorities.
    """
    # Include only user-side requests
    df_filtered = df[df['Alert Type'].isin(user_request_types)]

    return _plot_alerts_by_priority(
        df_filtered,
        'user_requests_with_priority.png',
        "User Requests by Types and Priorities"
    )

def _plot_alerts_by_priority(df, filename, title):
    """
    Helper function to create a bar chart for alerts by types with a breakdown by priorities.
    """
    # Create a pivot table
    alert_priority_counts = df.groupby(['Alert Type', 'Priority Level']).size().reset_index(name='Counts')
    alert_priority_pivot = alert_priority_counts.pivot(index='Alert Type', columns='Priority Level', values='Counts').fillna(0)

    # Sort alert types by total count
    alert_totals = alert_priority_pivot.sum(axis=1)
    alert_priority_pivot = alert_priority_pivot.loc[alert_totals.sort_values(ascending=False).index]

    # Dynamically set the figure height based on the number of alert types
    num_alert_types = len(alert_priority_pivot.index)
    fig = plt.figure(figsize=(12, max(6, num_alert_types * 0.5)))

    # Get the priority levels in the correct order
    priority_levels = ['P1', 'P2', 'P3', 'Cancelled', 'Other']
    alert_priority_pivot = alert_priority_pivot.reindex(columns=priority_levels, fill_value=0)

    # Get colors for the priorities
    colors = [priority_colors.get(level, '#95A5A6') for level in priority_levels]

    # Plot a stacked horizontal bar chart
    ax = alert_priority_pivot.plot(kind='barh', stacked=True, figsize=(12, max(6, num_alert_types * 0.5)), color=colors)

    plt.title(title, fontsize=16)
    plt.xlabel('Count', fontsize=14)
    plt.ylabel('Alert Type', fontsize=14)

    # Increase margins to prevent labels from being cut off
    plt.subplots_adjust(left=0.4, right=0.95, top=0.95, bottom=0.05)

    # Set font size for axis labels
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=10)

    # Align labels to the left
    ax.yaxis.set_tick_params(pad=10)
    for label in ax.get_yticklabels():
        label.set_horizontalalignment('left')

    # Move the legend outside the plot
    plt.legend(title='Priority', bbox_to_anchor=(1.0, 1), loc='upper left', fontsize=12)

    return fig

def plot_priority_levels(df):
    """
    Function to visualize the number of alerts by priority levels.
    """
    plt.figure(figsize=(6, 4))
    priority_order = ['P1', 'P2', 'P3', 'Cancelled', 'Other']

    # Use 'hue' parameter for color assignment
    ax = sns.countplot(
        data=df,
        x='Priority Level',
        hue='Priority Level',
        order=priority_order,
        palette=priority_colors,
        dodge=False
    )

    # Remove legend if it exists
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()

    plt.title('Number of Alerts by Priority Levels')
    plt.xlabel('Priority')
    plt.ylabel('Count')
    plt.tight_layout()

    # Return the figure instead of saving it
    return plt.gcf()

def plot_p1_alerts(df):
    """
    Function to create an image with a list of P1 alerts (ID and summaries).
    """
    p1_alerts = df[df['Priority Level'] == 'P1'][['Issue key', 'Summary']]

    if p1_alerts.empty:
        print("No P1 alerts.")
        return None

    # Create a table using matplotlib
    fig = plt.figure(figsize=(12, len(p1_alerts) * 0.5 + 1))
    plt.axis('off')
    table = plt.table(cellText=p1_alerts.values, colLabels=p1_alerts.columns, loc='center', cellLoc='left')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.auto_set_column_width(col=list(range(len(p1_alerts.columns))))

    plt.title('List of P1 Alerts')
    plt.tight_layout()

    return fig
