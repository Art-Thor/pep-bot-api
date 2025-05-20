# src/data_loader.py

import os
import sys
import pandas as pd
import argparse
from jira import JIRA

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT, REPORT_DAYS

def load_data(file_path):
    """
    Function to load data from a CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None

def fetch_jira_data():
    """
    Fetch data from Jira API.
    """
    jira = JIRA(
        server=JIRA_URL,
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
    )
    
    jql = f'project = {JIRA_PROJECT} AND created >= -{REPORT_DAYS}d ORDER BY createdDate DESC'
    issues = jira.search_issues(jql_str=jql, maxResults=False)
    
    records = []
    for issue in issues:
        fields = issue.fields
        records.append({
            'Issue key': issue.key,
            'Summary': fields.summary,
            'Status': fields.status.name if fields.status else 'Unknown',
            'Priority': fields.priority.name if fields.priority else 'Unassigned',
            'Assignee': fields.assignee.displayName if fields.assignee else 'Unassigned',
            'Created': fields.created,
            'Updated': fields.updated
        })
    
    return pd.DataFrame(records)

def main():
    parser = argparse.ArgumentParser(description='Fetch and save Jira data')
    parser.add_argument('--out', required=True, help='Output JSON file path')
    args = parser.parse_args()
    
    # Fetch data from Jira
    df = fetch_jira_data()
    
    # Save to JSON
    df.to_json(args.out, orient='records', date_format='iso')
    print(f"Data saved to {args.out}")

if __name__ == '__main__':
    main()
