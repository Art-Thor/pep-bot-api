import os
import logging
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN
from jira_handler import JiraHandler
from report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)

# Initialize handlers
jira_handler = JiraHandler()
report_generator = ReportGenerator()

@app.command("/jira-report")
def handle_jira_report(ack, body, client):
    """Handle the /jira-report command."""
    # Acknowledge the command immediately
    ack()

    user_id = body.get('user_id')
    channel_id = body.get('channel_id')

    # Notify user that the report generation has started
    try:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="🔄 Генерация отчёта запущена, это может занять несколько минут..."
        )
    except SlackApiError as e:
        logger.warning(f"Failed to send start notification: {e.response['error']}")

    try:
        # Generate the report (blocking)
        report_path = report_generator.generate_report(jira_handler)

        # Prepare the title with week number
        week_number = datetime.now().isocalendar()[1] - 1
        title = f"Jira Report – Week {week_number}"

        # Upload the report file to Slack
        client.files_upload(
            channels=channel_id,
            file=report_path,
            title=title,
            initial_comment="✅ Отчёт готов и отправлен!"
        )
        logger.info(f"Report uploaded: {report_path}")

    except Exception as e:
        # Log exception
        logger.exception("Error generating or uploading report")
        # Notify user about the error
        try:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"❌ Ошибка при генерации отчёта: {e}"
            )
        except SlackApiError:
            logger.error("Failed to send error notification to user")


def main():
    """Start the Slack bot in Socket Mode."""
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()


if __name__ == "__main__":
    main()
