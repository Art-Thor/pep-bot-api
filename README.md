# Jira Report Slack Bot

This Slack bot generates weekly Jira reports with visualizations and analytics.

## Features

- Generates comprehensive weekly Jira reports
- Creates visualizations for ticket distribution
- Tracks P1 tickets and priority changes
- Monitors cluster and namespace statistics
- Generates PDF reports with executive summaries

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
JIRA_URL=your-jira-instance-url
JIRA_EMAIL=your-email
JIRA_API_TOKEN=your-api-token
```

3. Run the bot:
```bash
python main.py
```

## Usage

Use the `/jira-report` command in Slack to generate a weekly report. The bot will:
1. Collect data from Jira
2. Generate visualizations
3. Create a PDF report
4. Upload the report to the channel

## Report Contents

- Executive Summary
- P1 Ticket Analysis
- Priority Distribution
- Cluster Statistics
- Namespace Analysis
- Valid/Invalid Alerts Trends
- Category Analytics
- Priority Changes

## Docker & Kubernetes Deployment

### Build Docker Image

```bash
docker build -t jira-report-bot .
```

### Environment Variables

The bot requires a `.env` file or environment variables for:
- SLACK_BOT_TOKEN
- SLACK_APP_TOKEN
- JIRA_URL
- JIRA_EMAIL
- JIRA_API_TOKEN
- ALLOWED_USER_IDS (comma-separated Slack user IDs)
- (other config as needed)

### Run with Docker

```bash
docker run --env-file .env jira-report-bot
```

### Kubernetes Example

Create a Kubernetes Secret or ConfigMap with your .env variables, then use a Deployment like:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jira-report-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jira-report-bot
  template:
    metadata:
      labels:
        app: jira-report-bot
    spec:
      containers:
      - name: jira-report-bot
        image: jira-report-bot:latest
        envFrom:
        - secretRef:
            name: jira-report-bot-env
        # or use configMapRef if not secret
```

**Note:**
- This bot does not expose HTTP ports; it connects to Slack via Socket Mode.
- Ensure outbound internet access for Slack and Jira API.
- Only one replica is recommended unless you use distributed locks for Slack events. 