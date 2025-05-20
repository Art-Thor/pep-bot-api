import requests
from datetime import datetime, timedelta
import logging
from config import (
    JIRA_URL,        # base URL, for example https://pepsico-ecomm.atlassian.net
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    REPORT_DAYS,
    CONFLUENCE_POSTMORTEM_PARENT
)

logger = logging.getLogger(__name__)

class ConfluenceHandler:
    def __init__(self):
        self.base = JIRA_URL.rstrip('/')
        self.auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    def get_recent_postmortems(self):
        # Calculate date N days ago
        cutoff = datetime.utcnow() - timedelta(days=REPORT_DAYS)
        date_str = cutoff.strftime('%Y-%m-%d')  # date only!

        # Build CQL query
        cql = (
            f'space = ECOMM AND type = page '
            f'AND ancestor = {CONFLUENCE_POSTMORTEM_PARENT} '
            f'AND created > "{date_str}"'
        )

        url = f'{self.base}/wiki/rest/api/content/search'
        params = {
            'cql': cql,
            'limit': 50,
            'expand': 'history,body.view'
        }

        try:
            resp = requests.get(url, auth=self.auth, params=params, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f'Failed to fetch post-mortem pages: {e}')
            return []

        results = resp.json().get('results', [])
        postmortems = []
        for page in results:
            postmortems.append({
                'id': page['id'],
                'title': page['title'],
                'created': page['history']['createdDate'][:10],
                'link': f"{self.base}/wiki{page['_links']['webui']}"
            })
        return postmortems 