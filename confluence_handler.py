import requests
from datetime import datetime, timedelta
import logging
from config import (
    JIRA_URL,        # базовый URL, например https://pepsico-ecomm.atlassian.net
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
        """
        Возвращает список страниц Confluence, которые:
        - находятся в пространстве ECOMM
        - являются потомками страницы с ID=CONFLUENCE_POSTMORTEM_PARENT
        - созданы за последние REPORT_DAYS дней
        """
        # Считаем дату начала
        start = datetime.utcnow() - timedelta(days=REPORT_DAYS)
        start_iso = start.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        # CQL-запрос
        cql = (
            f'space = ECOMM AND type = page '
            f'AND ancestor = {CONFLUENCE_POSTMORTEM_PARENT} '
            f'AND created > "{start_iso}"'
        )

        url = f'{self.base}/wiki/rest/api/content/search'
        params = {
            'cql': cql,
            'limit': 50,
            'expand': 'history'
        }

        try:
            resp = requests.get(url, auth=self.auth, params=params, timeout=10)
            resp.raise_for_status()
            results = resp.json().get('results', [])
            logger.info(f"Found {len(results)} recent post-mortem pages")

            # Формируем список словарей
            postmortems = []
            for page in results:
                postmortems.append({
                    'id': page['id'],
                    'title': page['title'],
                    'created': page['history']['createdDate'],
                    'link': f"{self.base}/wiki{page['_links']['webui']}"
                })
            return postmortems
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch post-mortem pages: {e}")
            return [] 