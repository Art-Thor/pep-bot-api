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