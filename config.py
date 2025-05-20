import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Slack configuration ===
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')

# === Jira configuration ===
JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
# Enable API-based data fetching instead of static dumps
USE_JIRA_API = True
# Pagination size for Jira API requests
JIRA_PAGE_SIZE = int(os.getenv('JIRA_PAGE_SIZE', 50))
JIRA_REQUEST_TIMEOUT = float(os.getenv('JIRA_REQUEST_TIMEOUT', 10))

# === Report configuration ===
REPORT_TITLE = os.getenv('REPORT_TITLE', "Pepsico Weekly Report")
JIRA_PROJECT = os.getenv('JIRA_PROJECT', "ISD")
REPORT_DAYS = int(os.getenv('REPORT_DAYS', 7))

# === JQL templates ===
JQL_TEMPLATES = {
    'all_tickets': (
        'project = {project} '
        'AND created >= -{days}d '
        'ORDER BY createdDate DESC'
    ),
    'p1_tickets': (
        'project = {project} '
        'AND priority = Highest '
        'AND created >= -{days}d '
        'ORDER BY createdDate DESC'
    ),
    'unclassified_tickets': (
        'project = {project} '
        'AND created >= -{days}d '
        'AND priority NOT IN (Highest, High, Medium) '
        'ORDER BY createdDate DESC'
    ),
}

# === Data processing settings ===
# Patterns for extracting cluster and namespace
EXTRACTION_PATTERNS = {
    'cluster': r"(?i)(?:cluster|k8s|kubernetes)[\s-]+([a-zA-Z0-9-]+)",
    'namespace': r"(?i)(?:namespace|ns)[\s-]+([a-zA-Z0-9-]+)"
}

# === Classification settings ===
# Map raw priorities to normalized categories
PRIORITY_MAP = {
    'Highest': 'P1',
    'High':    'P2',
    'Medium':  'P3',
    'Low':     'P4',
    'Unassigned': 'Unknown'
}

# === Cancelled/Resolved tickets identification ===
CANCELLED_KEYWORDS = [
    'cancelled',
    'resolved',
    'closed'
]

# === Visualization settings ===
CHART_COLORS = {
    'P1': '#FF0000',  # red for highest
    'P2': '#FFA500',  # orange for high
    'P3': '#FFFF00',  # yellow for medium
    'P4': '#00FF00',  # green for low
    'Unknown': '#808080'  # grey for unassigned/other
}

# === Paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, 'reports')
CHART_DIR = os.path.join(BASE_DIR, 'charts')

# Create directories if not exist (at import time)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

# === Other settings ===
# Whether to cache Jira API responses locally
ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'false').lower() == 'true'
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', 3600))
