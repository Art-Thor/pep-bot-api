import os
from datetime import datetime
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from config import REPORT_DIR, CHART_DIR, REPORT_TITLE, USE_JIRA_API
from jira_handler import JiraHandler
from confluence_handler import ConfluenceHandler

# Old visualization utilities
from visualization import (
    plot_priority_levels,
    plot_cluster_distribution,
    plot_namespace_distribution,
    plot_p1_alerts
)

class ReportGenerator:
    def __init__(self):
        # Prepare styles and directories
        self.styles = getSampleStyleSheet()
        os.makedirs(REPORT_DIR, exist_ok=True)
        os.makedirs(CHART_DIR, exist_ok=True)
        # Initialize handlers
        self.conf_handler = ConfluenceHandler()

    def _create_trend_chart(self, trend_data):
        """Create a simple line chart for weekly trends using pandas built-in"""
        # Save chart as PNG
        chart_path = os.path.join(CHART_DIR, 'weekly_trend.png')
        ax = trend_data.plot(x='week', y='count', legend=False)
        ax.set_title('Weekly Trend')
        ax.set_xlabel('Week')
        ax.set_ylabel('Count')
        fig = ax.get_figure()
        fig.tight_layout()
        fig.savefig(chart_path)
        fig.clear()
        return chart_path

    def generate_report(self, jira_handler: JiraHandler) -> str:
        """Generate the complete report as a PDF and return its path."""
        # Fetch data via API
        df = jira_handler.get_all_tickets()

        # Charts using old widgets
        priority_chart = plot_priority_levels(df)
        cluster_chart = plot_cluster_distribution(df)
        namespace_chart = plot_namespace_distribution(df)

        # Weekly trend
        trend_df = jira_handler.get_weekly_trend()
        trend_chart = self._create_trend_chart(trend_df)

        # P1 alerts table image
        p1_alerts_image = plot_p1_alerts(df)

        # Build PDF
        week_number = datetime.now().isocalendar()[1] - 1
        report_path = os.path.join(REPORT_DIR, f'weekly_report_w{week_number}.pdf')
        doc = SimpleDocTemplate(report_path, pagesize=letter)
        story = []

        # Title
        title_style = ParagraphStyle(
            'Title', parent=self.styles['Heading1'], fontSize=24, spaceAfter=20
        )
        story.append(Paragraph(f"{REPORT_TITLE} - Week {week_number}", title_style))
        story.append(Spacer(1, 12))

        # Executive Summary
        summary_style = self.styles['Normal']
        total_tickets = len(df)
        p1_count = len(df[df['priority'] == 'P1'])
        cancelled_count = df['status'].str.lower().isin(['cancelled', 'closed', 'resolved']).sum()
        story.append(Paragraph("<b>Executive Summary</b>", self.styles['Heading2']))
        story.append(Paragraph(
            f"Total Tickets: {total_tickets}<br/>"
            f"P1 Tickets: {p1_count}<br/>"
            f"Cancelled/Resolved: {cancelled_count}",
            summary_style
        ))
        story.append(Spacer(1, 12))

        # Post Mortems section
        pm = self.conf_handler.get_recent_postmortems()
        story.append(Paragraph("P1 — Post Mortems", self.styles['Heading2']))
        if not pm:
            story.append(Paragraph("No Post Mortems created in the last week.", self.styles['Normal']))
        else:
            for item in pm:
                story.append(Paragraph(
                    f"- <a href=\"{item['link']}\">{item['title']}</a> "
                    f"({item['created'][:10]})",
                    self.styles['Normal']
                ))
        story.append(Spacer(1, 12))

        # Insert charts
        for title, path in [
            ('Priority Distribution', priority_chart),
            ('Cluster Distribution', cluster_chart),
            ('Namespace Distribution', namespace_chart),
            ('Weekly Trend', trend_chart)
        ]:
            story.append(Paragraph(title, self.styles['Heading2']))
            story.append(Image(path, width=6*inch, height=4*inch))
            story.append(Spacer(1, 12))

        # P1 Alerts
        story.append(Paragraph("P1 Alerts", self.styles['Heading2']))
        story.append(Image(p1_alerts_image, width=6*inch, height=4*inch))
        story.append(Spacer(1, 12))

        # Build and save
        doc.build(story)
        return report_path
