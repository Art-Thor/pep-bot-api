#src/main.py

import os
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data
from data_cleaning import clean_data
from classification import classify_alerts, define_priority
from visualization import (
    plot_priority_levels,
    plot_priority_pie,
    plot_alert_types_with_priority,
    plot_user_requests_by_priority,
    plot_p1_alerts,
    plot_cancellation_reasons
)

def generate_cancellation_file(df, output_file):
    """
    Generate a text file with canceled tickets for manual input of cancellation reasons.
    """
    # Убедимся, что 'Assignee' не содержит NaN
    df['Assignee'] = df['Assignee'].fillna('Unassigned')

    # Используем 'Status' вместо 'Priority Level'
    canceled_tickets = df[
        (df['Status'].str.lower() == 'canceled') &
        (df['Assignee'].str.contains('oleg.kolomiets.contractor|max.ivanchenko|arthur holubov|unassigned', na=False))
    ][['Issue key', 'Summary']]

    print("Filtered canceled tickets:")
    print(canceled_tickets)  # Проверка на фильтрацию

    if canceled_tickets.empty:
        print("No canceled tickets found.")
        return
    
    # Генерация файла
    with open(output_file, 'w') as f:
        f.write("Ticket ID\tSummary\tReason\n")
        for _, row in canceled_tickets.iterrows():
            f.write(f"{row['Issue key']}\t{row['Summary']}\tNo Reason Provided\n")
    print(f"Cancelled tickets saved to {output_file}.")

def generate_report(df, outdir):
    """
    Generate all report visualizations and save them to the output directory.
    """
    os.makedirs(outdir, exist_ok=True)
    
    # Priority Distribution
    fig = plot_priority_levels(df)
    fig.savefig(os.path.join(outdir, 'priority_distribution.png'), bbox_inches='tight')
    plt.close(fig)
    
    # Cluster Distribution
    fig = plot_alert_types_with_priority(df)
    fig.savefig(os.path.join(outdir, 'cluster_distribution.png'), bbox_inches='tight')
    plt.close(fig)
    
    # Namespace Distribution
    fig = plot_user_requests_by_priority(df)
    fig.savefig(os.path.join(outdir, 'namespace_distribution.png'), bbox_inches='tight')
    plt.close(fig)
    
    # Weekly Trend
    fig = plot_priority_pie(df)
    fig.savefig(os.path.join(outdir, 'weekly_trend.png'), bbox_inches='tight')
    plt.close(fig)
    
    # P1 Alerts
    fig = plot_p1_alerts(df)
    if fig is not None:  # Only save if we have P1 alerts
        fig.savefig(os.path.join(outdir, 'p1_alerts.png'), bbox_inches='tight')
        plt.close(fig)
    else:
        # Create an empty figure with a message
        fig = plt.figure(figsize=(8, 4))
        plt.axis('off')
        plt.text(0.5, 0.5, 'No P1 alerts in the current period', 
                horizontalalignment='center',
                verticalalignment='center',
                transform=plt.gca().transAxes,
                fontsize=14)
        plt.tight_layout()
        fig.savefig(os.path.join(outdir, 'p1_alerts.png'), bbox_inches='tight')
        plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description='Generate legacy report visualizations')
    parser.add_argument('--dump', required=True, help='Input JSON file path')
    parser.add_argument('--outdir', required=True, help='Output directory for visualizations')
    args = parser.parse_args()
    
    # Load data
    df = pd.read_json(args.dump)
    
    # Process data
    df = clean_data(df)
    df = classify_alerts(df)
    df = define_priority(df)
    
    # Generate visualizations
    generate_report(df, args.outdir)
    print(f"Visualizations saved to {args.outdir}")

if __name__ == '__main__':
    main()
