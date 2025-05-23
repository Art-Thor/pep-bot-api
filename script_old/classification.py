# src/classification.py

import re
from config import PRIORITY_MAP

def classify_alerts(df):
    """
    Function to classify alerts based on patterns in the 'Summary' field.
    """
    def get_alert_type(summary):
        summary_lower = str(summary).lower()
        
        patterns = [
            # New pattern to classify 'mbt' tickets
            (r'mbt', 'MBT'),
            # Combined pattern for 'Change Request' and 'Team Change Request'
            (r'\b(team )?change request\b', 'Change Request'),
            # Troubleshooting Requests
            (r'\btroubleshooting\b.*', 'Troubleshooting'),
            # Password Reset Requests
            (r'\bpassword reset request\b.*', 'Password Reset Request'),
            # User Provisioning Requests
            (r'\buser provisioning request\b.*', 'User Provisioning Request'),
            # Terraform Failures
            (r'\bterraform failed to generate plan\b.*', 'Terraform Plan Failed'),
            # Snowflake Public Key
            (r'\bsnowflake public key\b.*', 'Snowflake Public Key'),
            # High CPU Utilization with dynamic info
            (r'\bcpu utilization above.*?on (\S+)', lambda m: f"High CPU Utilization on {m.group(1)}"),
            # Outage Reporting with dynamic info
            (r'\boutage reporting\b.*?for (\S+)', lambda m: f"Outage Reporting for {m.group(1)}"),
            # Kubernetes Cluster Names and Hosts
            (r'kube_cluster_name:(\S+)', lambda m: m.group(1)),
            # Team Change Requests
            (r'\bteam change\b', 'Team Change Request'),
            # Troubleshooting Requests
            (r'\btroubleshooting\b', 'Troubleshooting'),
            # Password Reset Requests
            (r'\bpassword reset request\b', 'Password Reset Request'),
            # User Provisioning Requests
            (r'\buser provisioning request\b', 'User Provisioning Request'),
            # Terraform Failures
            (r'\bterraform failed to generate plan\b', 'Terraform Plan Failed'),
            # Snowflake Public Key
            (r'\bsnowflake public key\b', 'Snowflake Public Key'),
            # High CPU Utilization
            (r'\bcpu utilization above\b', 'High CPU Utilization'),
            # Change Requests
            (r'\bchange request\b', 'Change Request'),
            # Outage Reporting
            (r'\boutage reporting\b', 'Outage Reporting'),
            # Kubernetes Cluster Names
            (r'kube_cluster_name:apps-prod-01', 'apps-prod-01'),
            (r'kube_cluster_name:ecomm-prod01-scus1', 'ecomm-prod01-scus1'),
            (r'kube_cluster_name:ecomm-prod-scus1', 'ecomm-prod01-scus1'),
            (r'kube_cluster_name:de-airflow-production', 'de-airflow-production'),
            (r'kube_cluster_name:de-airflow-staging', 'de-airflow-staging'),
            (r'kube_cluster_name:airflow-prod-01', 'airflow-prod-01'),
            (r'kube_cluster_name:cdp-production', 'cdp-production'),
            (r'kube_cluster_name:cdp-staging', 'cdp-staging'),
            (r'kube_cluster_name:pepdirect', 'pepdirect'),
            (r'kube_cluster_name:automation-api-heartbeat', 'Automation API Heartbeat'),
            (r'kube_cluster_name:terraform-drift', 'terraform drift'),
            (r'kube_cluster_name:wiz-finding', 'Wiz findings'),
            (r'kube_cluster_name:wiz', 'wiz'),
            (r'airflow2 cdp', 'cdp-staging'),
            # Cluster Names without prefix
            (r'\bapps-prod-01\b', 'apps-prod-01'),
            (r'\becomm-prod01-scus1\b', 'ecomm-prod01-scus1'),
            (r'\becomm-prod-scus1\b', 'ecomm-prod01-scus1'),
            (r'\bde-airflow-production\b', 'de-airflow-production'),
            (r'\bde-airflow-staging\b', 'de-airflow-staging'),
            (r'\bairflow-prod-01\b', 'airflow-prod-01'),
            (r'\bcdp-production\b', 'cdp-production'),
            (r'\bcdp-staging\b', 'cdp-staging'),
            (r'\bstaging cdp\b', 'cdp-staging'),
            (r'\bpepdirect\b', 'pepdirect'),
            (r'\bautomation api heartbeat\b', 'Automation API Heartbeat'),
            # Other Keywords
            (r'\bterraform drift\b', 'terraform drift'),
            (r'\bwiz finding\b', 'Wiz findings'),
            (r'\bwiz\b', 'wiz'),
            (r'\baws guardduty\b', 'AWS GuardDuty'),
            (r'\bsnyk\b', 'Snyk'),
            (r'\bgha\b', 'GHA'),
            (r'\bgithub actions\b', 'GHA'),
            (r'\bebs volume\b', 'EBS Volume'),
            (r'\bebs volumes\b', 'EBS Volume'),
            (r'\bcert-manager\b', 'cert-manager'),
            (r'\bairflow-dpi\b', 'airflow-dpi'),
            (r'\bsimple-machine\b', 'simple-machine'),
            # Add additional patterns if necessary
        ]

        for pattern, category in patterns:
            match = re.search(pattern, summary_lower)
            if match:
                if callable(category):
                    return category(match)
                else:
                    return category

        return 'Other'

    df['Alert Type'] = df['Summary'].apply(get_alert_type)

    # Вывод тикетов из категории 'Other' для анализа
    others = df[df['Alert Type'] == 'Other']
    if not others.empty:
        print("Tickets that fell into the 'Other' category:")
        print(others[['Issue key', 'Summary']])
    
    return df

def define_priority(df):
    """
    Function to determine the priority of an alert.
    """
    # Normalize and map priorities case-insensitively
    norm_priority = df['Priority'].astype(str).str.strip().str.title()
    mapped = norm_priority.map(PRIORITY_MAP)
    # If status is canceled, mark as Cancelled
    status = df['Status'].astype(str).str.lower()
    cancelled_mask = status.isin(['canceled', 'cancelled', 'closed', 'resolved'])
    df['Priority Level'] = mapped.fillna(norm_priority)
    df.loc[cancelled_mask, 'Priority Level'] = 'Cancelled'
    return df
