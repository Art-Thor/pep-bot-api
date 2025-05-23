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

def clean_data(df):
    """Clean and prepare the data for visualization."""
    # Ensure required columns exist
    if 'summary' not in df.columns:
        df['summary'] = df.get('Summary', '')
    if 'priority' not in df.columns:
        df['priority'] = df.get('Priority', '')
    if 'status' not in df.columns:
        df['status'] = df.get('Status', '')
    
    # Convert to string type to avoid any type issues
    df['summary'] = df['summary'].astype(str)
    df['priority'] = df['priority'].astype(str)
    df['status'] = df['status'].astype(str)
    
    return df

def align_columns(df):
    """
    Приводим заголовки к lower case и дублируем critical поля,
    чтобы дальше всегда был df['priority'], df['summary'] и т.п.
    """
    rename_map = {c: c.lower() for c in df.columns}
    df = df.rename(columns=rename_map)
    # legacy-совместимость: создаём alias, если нужно
    if "priority" not in df.columns and "Priority" in rename_map:
        df["priority"] = df["Priority"]
    if "summary" not in df.columns and "Summary" in rename_map:
        df["summary"] = df["Summary"]
    if "status" not in df.columns and "Status" in rename_map:
        df["status"] = df["Status"]
    if "assignee" not in df.columns and "Assignee" in rename_map:
        df["assignee"] = df["Assignee"]
    # Ensure 'alert type' is always lowercase
    if "Alert Type" in df.columns:
        df.rename(columns={"Alert Type": "alert type"}, inplace=True)
    return df

# PRIORITY_MAP для скрипта
PRIORITY_MAP = {
    "highest": "P1",
    "high":    "P2",
    "medium":  "P3",
    "low":     "P4",
    "lowest":  "P5",
    "cancelled": "Cancelled",
}

def classify_alerts(df):
    """Classify alerts into appropriate categories."""
    df = df.copy()
    # Initialize alert type column in lowercase
    df['alert type'] = 'Other'
    # Define patterns for classification
    patterns = {
        'Password Reset': ['password reset', 'reset password'],
        'Team Change': ['team change', 'change team'],
        'Access Management': ['access management', 'access managemen'],
        'User Provisioning': ['user provisioning', 'provision user'],
        'User Deprovisioning': ['user deprovisioning', 'deprovision user'],
        'Wiz Finding': ['wiz finding', 'wiz alert'],
        'GuardDuty': ['guardduty', 'guard duty'],
        'Snyk': ['snyk', 'vulnerability'],
        'Troubleshooting': ['troubleshooting', 'trouble shooting'],
        'Outage': ['outage', 'service down']
    }
    # Classify based on summary text
    for alert_type, keywords in patterns.items():
        mask = df['summary'].str.lower().str.contains('|'.join(keywords), case=False, na=False)
        df.loc[mask, 'alert type'] = alert_type
    return df

def define_priority(df):
    # align_columns(df) call removed!
    # присваиваем Priority Level, если ещё нет
    if "priority level" not in df.columns:
        df["Priority Level"] = (
            df["priority"]
            .str.lower()
            .map(PRIORITY_MAP)
            .fillna("Other")
        )
    # если нужен фильтр P1-тикетов
    return df

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
    df = align_columns(df)
    
    # Process data
    df = clean_data(df)
    df = classify_alerts(df)
    df = define_priority(df)
    
    # Print some debug information
    print("\nDataFrame columns:", df.columns.tolist())
    print("\nUnique Alert Types:", df['alert type'].unique())
    print("\nUnique Priority Levels:", df['Priority Level'].unique())
    
    # Generate visualizations
    generate_report(df, args.outdir)
    print(f"Visualizations saved to {args.outdir}")

if __name__ == '__main__':
    main()

    # Unit test for priority mapping
    test_df = pd.DataFrame({
        'Issue key': ['TEST-1'],
        'Summary': ['Test summary'],
        'Status': ['Open'],
        'Priority': ['Highest'],
        'Assignee': ['user']
    })
    test_df = align_columns(test_df)  # Ensure lowercase columns for test
    result = define_priority(test_df)
    assert (result['Priority Level'] == 'P1').any(), "Priority mapping failed: 'Highest' should map to 'P1'"
    print("Unit test passed: 'Highest' is mapped to 'P1' in Priority Level.")
