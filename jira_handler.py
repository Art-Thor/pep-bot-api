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
    ENABLE_CACHING, CACHE_TTL_SECONDS, CLUSTERS, NAMESPACES,
    ALERT_SOURCES
)
from data_cleaning import clean_dataframe
from classification import classify_priorities, assign_alert_type

logger = logging.getLogger(__name__)

# One place to maintain all "bot" accounts we want to ignore
IGNORED_PRIORITY_AUTHORS = {
    "automation-for-jira",          # accountId or key
    "Automation for Jira",          # displayName fallback
}

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
        # Priority change history
        self._priority_history = {}

    def _track_priority_change(self, issue_key: str, new_priority: str, timestamp: datetime = None):
        """Track priority changes for a ticket."""
        if timestamp is None:
            timestamp = datetime.now()
            
        if issue_key not in self._priority_history:
            self._priority_history[issue_key] = []
            
        self._priority_history[issue_key].append({
            'priority': new_priority,
            'timestamp': timestamp
        })

    def get_priority_history(self, issue_key: str = None):
        """Get priority change history for a specific ticket or all tickets."""
        if issue_key:
            return self._priority_history.get(issue_key, [])
        return self._priority_history

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
            updated = getattr(fields, 'updated', None)
            assignee = fields.assignee.displayName if fields.assignee else 'Unassigned'
            resolution = fields.resolution.name if fields.resolution else ''
            
            # --- priority-change history ------------------------------------- #
            # Pull the full issue with changelog so we can see *who* changed it
            try:
                issue_full = self.jira.issue(issue.key, expand="changelog")
            except Exception as e:
                logger.warning(f"Cannot expand changelog for {issue.key}: {e}")
                issue_full = None

            if issue_full and hasattr(issue_full, "changelog"):
                for history in issue_full.changelog.histories:
                    author_id   = getattr(history.author, "accountId", None) or getattr(history.author, "key", "")
                    author_name = history.author.displayName

                    # Skip if the author is in the ignore-list (by id OR name)
                    if author_id in IGNORED_PRIORITY_AUTHORS or author_name in IGNORED_PRIORITY_AUTHORS:
                        continue

                    for item in history.items:
                        if item.field == "priority":
                            self._track_priority_change(
                                issue.key,
                                f"{item.fromString}->{item.toString}",
                                datetime.strptime(history.created[:19], "%Y-%m-%dT%H:%M:%S"),
                            )
            
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
                'updated': updated,
                'cluster': cluster,
                'namespace': namespace,
                'assignee': assignee,
                'resolution': resolution,
                'cancelled': cancelled_flag
            })
        
        df = pd.DataFrame(records)
        # Early return if empty
        if df.empty:
            return df

        # Apply data cleaning and classification pipeline
        df = clean_dataframe(df)
        df = classify_priorities(df)
        df = assign_alert_type(df)
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

    def get_cluster_alert_counts(self) -> dict[str, int]:
        """
        For each cluster in CLUSTERS, counts the number of tickets:
        - using JQL template 'cluster_alerts'
        - excluding status 'cancelled' and assignee 'oleg.kolomiets.contractor'
        """
        counts: dict[str, int] = {}
        for cluster in CLUSTERS:
            jql = JQL_TEMPLATES['cluster_alerts'].format(
                project=JIRA_PROJECT,
                cluster=cluster,
                days=REPORT_DAYS
            )
            issues = self.jira.search_issues(jql_str=jql)
            df = self._to_dataframe(issues)
            df = clean_dataframe(df)

            # If empty - set 0 and continue
            if df.empty:
                counts[cluster] = 0
                continue

            # Filter out cancelled
            if 'status' in df.columns:
                df = df[~df['status'].str.lower().eq('cancelled')]
            # Filter out "duplicates" by assignee
            if 'assignee' in df.columns:
                df = df[df['assignee'] != 'oleg.kolomiets.contractor']

            counts[cluster] = len(df)
        return counts

    def get_namespace_alert_counts(self) -> dict[str, int]:
        """
        For each namespace in NAMESPACES, counts the number of tickets:
        - using JQL template 'namespace_alerts'
        - excluding status 'cancelled' and assignee 'oleg.kolomiets.contractor'
        """
        counts: dict[str, int] = {}
        for ns in NAMESPACES:
            try:
                jql = JQL_TEMPLATES['namespace_alerts'].format(
                    project=JIRA_PROJECT,
                    namespace=ns,
                    days=REPORT_DAYS
                )
                issues = self.jira.search_issues(jql_str=jql)
                df = self._to_dataframe(issues)
                df = clean_dataframe(df)

                if df.empty:
                    counts[ns] = 0
                    continue

                if 'status' in df.columns:
                    df = df[~df['status'].str.lower().eq('cancelled')]
                if 'assignee' in df.columns:
                    df = df[df['assignee'] != 'oleg.kolomiets.contractor']

                counts[ns] = len(df)
            except Exception as e:
                logger.error(f"Error getting alerts for namespace {ns}: {str(e)}")
                counts[ns] = 0  # Set count to 0 on error
                continue

        return counts

    def get_source_alert_counts(self) -> dict[str, int]:
        """
        For each term in ALERT_SOURCES counts the number of tickets:
        - using JQL template 'text_triaged' (NOC Representative != EMPTY)
        - excluding status 'cancelled' and assignee 'oleg.kolomiets.contractor'
        """
        counts: dict[str, int] = {}
        for term in ALERT_SOURCES:
            jql = JQL_TEMPLATES['text_triaged'].format(
                project=JIRA_PROJECT,
                term=term,
                days=REPORT_DAYS
            )
            issues = self.jira.search_issues(jql_str=jql)
            df = self._to_dataframe(issues)
            df = clean_dataframe(df)

            if df.empty:
                counts[term] = 0
                continue

            # Filter out cancelled
            if 'status' in df.columns:
                df = df[~df['status'].str.lower().eq('cancelled')]
            # Filter out duplicates
            if 'assignee' in df.columns:
                df = df[df['assignee'] != 'oleg.kolomiets.contractor']

            counts[term] = len(df)
        return counts

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

    def get_weekly_valid_alerts_by_cluster(self, weeks: int = 5) -> pd.DataFrame:
        """
        Returns DataFrame of size len(CLUSTERS)×weeks, 
        where df.loc[cluster, i] = count valid issues for cluster in week i.
        Week 0: created >= 0-7d ago, week 1: 7-14d ago, etc.
        Only includes tickets where NOC Representative is set (triaged).
        """
        # Initialize container
        data = {cluster: [] for cluster in CLUSTERS}
        
        # For each week from 0 to weeks-1
        for i in range(weeks):
            end = datetime.utcnow() - timedelta(days=7*i)
            start = end - timedelta(days=7)
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')

            # For each cluster
            for cluster in CLUSTERS:
                jql = (
                    f'project = {JIRA_PROJECT} '
                    f'AND text ~ "{cluster}" '
                    f'AND "NOC Representative[User Picker (single user)]" != EMPTY '
                    f'AND created >= "{start_str}" '
                    f'AND created < "{end_str}" '
                    f'ORDER BY createdDate DESC'
                )
                issues = self.jira.search_issues(jql_str=jql, maxResults=JIRA_PAGE_SIZE)
                df = self._to_dataframe(issues)
                df = clean_dataframe(df)

                # Apply filters
                if not df.empty:
                    if 'status' in df.columns:
                        df = df[~df['status'].str.lower().eq('cancelled')]
                    if 'assignee' in df.columns:
                        df = df[df['assignee'] != 'oleg.kolomiets.contractor']
                count = len(df) if not df.empty else 0
                data[cluster].append(count)

        # Create DataFrame with weeks as columns
        cols = [f'week {-i}' for i in range(weeks-1, -1, -1)]
        df = pd.DataFrame(data, index=cols).T  # transpose: now index=clusters, cols=weeks
        
        # Rename columns to actual week numbers
        current_week = datetime.utcnow().isocalendar()[1]
        df.columns = [f"week {current_week - i - 1}" for i in range(weeks)]
        
        return df

    def get_weekly_canceled_alerts_by_cluster(self, weeks: int = 5) -> pd.DataFrame:
        """
        Like get_weekly_valid_alerts_by_cluster, but counts only tickets that are:
          - status = Cancelled OR assignee = 'oleg.kolomiets.contractor'
          - triaged (NOC != EMPTY)
          - for each of the last `weeks` 7-day intervals.
        """
        data = {cluster: [] for cluster in CLUSTERS}
        now = datetime.utcnow()

        for i in range(weeks):
            end = now - timedelta(days=7 * i)
            start = end - timedelta(days=7)
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')

            for cluster in CLUSTERS:
                # Triaged = NOC != EMPTY
                jql = (
                    f'project = {JIRA_PROJECT} '
                    f'AND text ~ "{cluster}" '
                    f'AND "NOC Representative[User Picker (single user)]" != EMPTY '
                    f'AND created >= "{start_str}" '
                    f'AND created < "{end_str}" '
                    'ORDER BY createdDate DESC'
                )
                issues = self.jira.search_issues(jql_str=jql, maxResults=JIRA_PAGE_SIZE)
                df = self._to_dataframe(issues)
                df = clean_dataframe(df)

                if df.empty:
                    data[cluster].append(0)
                    continue

                # Keep only cancelled OR assigned to Oleg
                mask_cancelled = df['status'].str.lower().eq('cancelled')
                mask_oleg = df['assignee'].str.lower() == 'oleg.kolomiets.contractor'
                df_canceled = df[mask_cancelled | mask_oleg]

                data[cluster].append(len(df_canceled))

        # Create DataFrame, similar to valid alerts
        cols = [f'week {-i}' for i in range(weeks - 1, -1, -1)]
        df = pd.DataFrame(data, index=cols).T
        
        # Rename columns to actual week numbers
        current_week = datetime.utcnow().isocalendar()[1]
        df.columns = [f"week {current_week - i - 1}" for i in range(weeks)]
        
        return df
