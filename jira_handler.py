import logging
import re
from datetime import datetime, timedelta
from jira import JIRA
import pandas as pd
from config import (
    JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN,
    USE_JIRA_API, JIRA_PAGE_SIZE, JIRA_REQUEST_TIMEOUT,
    JIRA_PROJECT, REPORT_DAYS, JQL_TEMPLATES,
    EXTRACTION_PATTERNS, PRIORITY_MAP, CANCELLED_KEYWORDS,
    ENABLE_CACHING, CACHE_TTL_SECONDS
)
from data_cleaning import clean_dataframe
from classification import classify_priorities

logger = logging.getLogger(__name__)

class JiraHandler:
    def __init__(self):
        # Initialize Jira client only if API is enabled
        if USE_JIRA_API:
            self.jira = JIRA(
                server=JIRA_URL,
                basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
                timeout=JIRA_REQUEST_TIMEOUT
            )
        else:
            self.jira = None
            logger.warning("Jira API is disabled. Using static data only.")
        # Simple in-memory cache
        self._cache = {} if ENABLE_CACHING else None

    def _fetch_issues(self, template_key):
        """Fetch issues from Jira using JQL template with pagination."""
        if not USE_JIRA_API:
            logger.warning(f"Jira API is disabled. Cannot fetch issues for {template_key}")
            return []

        jql_template = JQL_TEMPLATES.get(template_key)
        if not jql_template:
            raise ValueError(f"Unknown JQL template: {template_key}")
        jql = jql_template.format(project=JIRA_PROJECT, days=REPORT_DAYS)
        # Check cache
        if ENABLE_CACHING and template_key in self._cache:
            timestamp, data = self._cache[template_key]
            age = (datetime.now() - timestamp).total_seconds()
            if age < CACHE_TTL_SECONDS:
                logger.debug(f"Using cached data for {template_key}")
                return data

        start_at = 0
        all_issues = []
        while True:
            issues = self.jira.search_issues(
                jql_str=jql,
                startAt=start_at,
                maxResults=JIRA_PAGE_SIZE
            )
            if not issues:
                break
            all_issues.extend(issues)
            if len(issues) < JIRA_PAGE_SIZE:
                break
            start_at += JIRA_PAGE_SIZE
        # Cache result
        if ENABLE_CACHING:
            self._cache[template_key] = (datetime.now(), all_issues)
        logger.info(f"Fetched {len(all_issues)} issues for '{template_key}'")
        return all_issues

    def _extract_pattern(self, summary, key):
        """Extract data by regex from summary using configured patterns."""
        pattern = EXTRACTION_PATTERNS.get(key)
        if not pattern:
            return 'Unknown'
        match = re.search(pattern, summary)
        return match.group(1) if match else 'Unknown'

    def _to_dataframe(self, issues):
        """Convert list of Jira issues to cleaned DataFrame."""
        records = []
        for issue in issues:
            fields = issue.fields
            summary = getattr(fields, 'summary', '')
            raw_priority = fields.priority.name if fields.priority else 'Unassigned'
            priority = PRIORITY_MAP.get(raw_priority, raw_priority)
            status = fields.status.name if fields.status else 'Unknown'
            created = getattr(fields, 'created', None)
            assignee = fields.assignee.displayName if fields.assignee else 'Unassigned'
            # Extraction
            cluster = self._extract_pattern(summary, 'cluster')
            namespace = self._extract_pattern(summary, 'namespace')
            # Cancelled detection
            lower_summary = summary.lower()
            cancelled_flag = any(kw in lower_summary or kw in status.lower() for kw in CANCELLED_KEYWORDS)

            records.append({
                'key': issue.key,
                'summary': summary,
                'priority': priority,
                'status': status,
                'created': created,
                'cluster': cluster,
                'namespace': namespace,
                'assignee': assignee,
                'cancelled': cancelled_flag
            })
        df = pd.DataFrame(records)
        # Apply data cleaning and classification
        df = clean_dataframe(df)
        df = classify_priorities(df)
        logger.debug(f"Converted {len(df)} issues to DataFrame")
        return df

    def get_all_tickets(self):
        """Return DataFrame of all tickets."""
        issues = self._fetch_issues('all_tickets')
        return self._to_dataframe(issues)

    def get_p1_tickets(self):
        """Return DataFrame of P1 (highest priority) tickets."""
        df = self.get_all_tickets()
        return df[df['priority'] == PRIORITY_MAP.get('Highest', 'Highest')]

    def get_unclassified_tickets(self):
        """Return DataFrame of unclassified tickets."""
        issues = self._fetch_issues('unclassified_tickets')
        return self._to_dataframe(issues)

    def get_priority_distribution(self):
        """Return Series of priority distribution counts."""
        df = self.get_all_tickets()
        return df['priority'].value_counts()

    def get_cluster_distribution(self):
        """Return Series of cluster distribution counts."""
        df = self.get_all_tickets()
        return df['cluster'].value_counts()

    def get_namespace_distribution(self):
        """Return Series of namespace distribution counts."""
        df = self.get_all_tickets()
        return df['namespace'].value_counts()

    def get_initial_troubleshooting_metrics(self):
        """Returns (total, untriaged, percent_triaged)."""
        total_issues = self._fetch_issues('isd_board_total')
        untriaged_issues = self._fetch_issues('isd_board_untriaged')

        total = len(total_issues)
        untriaged = len(untriaged_issues)

        # If no tasks or no untriaged - 100%
        if total == 0 or untriaged == 0:
            percent = 100.0
        else:
            percent = (total - untriaged) / total * 100.0

        return total, untriaged, percent

    def get_weekly_trend(self, weeks=5):
        """Return DataFrame with weekly ticket counts for last n weeks."""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        trend = []
        current = start_date
        while current < end_date:
            week_end = current + timedelta(days=7)
            # Create temporary JQL for trend
            jql = (
                f"project = {JIRA_PROJECT} "
                f"AND created >= \"{current.strftime('%Y-%m-%d')}\" "
                f"AND created < \"{week_end.strftime('%Y-%m-%d')}\""
            )
            # Use pagination to get all issues
            start_at = 0
            all_issues = []
            while True:
                issues = self.jira.search_issues(
                    jql_str=jql,
                    startAt=start_at,
                    maxResults=JIRA_PAGE_SIZE
                )
                if not issues:
                    break
                all_issues.extend(issues)
                if len(issues) < JIRA_PAGE_SIZE:
                    break
                start_at += JIRA_PAGE_SIZE
            trend.append({'week': current.strftime('%Y-%m-%d'), 'count': len(all_issues)})
            current = week_end
        df = pd.DataFrame(trend)
        logger.info("Generated weekly trend data")
        return df
