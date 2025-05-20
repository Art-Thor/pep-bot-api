#src/main.py

import os
from data_loader import load_data
from data_cleaning import clean_data
from classification import classify_alerts, define_priority
from visualization import (
    plot_priority_levels,
    plot_priority_pie,
    plot_alert_types_with_priority,
    plot_user_requests_by_priority,
    plot_p1_alerts,
    plot_cancellation_reasons  # Import the new function
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

def main():
    # Path to the data file
    data_file = '../data/jira_dump.csv'
    cancellation_file = '../reports/canceled_tickets.txt'
    
    # Step 1: Load data
    df = load_data(data_file)
    if df is None:
        return
    
    # Step 2: Clean data
    df = clean_data(df)
    
    # Step 3: Classify alerts
    df = classify_alerts(df)
    df = define_priority(df)
    
    # Step 4: Visualization
    plot_priority_levels(df)
    plot_priority_pie(df)
    plot_alert_types_with_priority(df)
    plot_user_requests_by_priority(df)
    plot_p1_alerts(df)

    # Step 5: Generate cancellation file
    generate_cancellation_file(df, cancellation_file)
    
    # Step 6 (Optional): Save processed data
    if not os.path.exists('../reports/'):
        os.makedirs('../reports/')
    df.to_csv('../reports/processed_data.csv', index=False)

if __name__ == '__main__':
    main()
