import os
import glob
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors, utils
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    KeepTogether, ListFlowable, ListItem
)
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
    plot_p1_alerts,
    plot_priority_changes,
    plot_ticket_table
)

class ReportGenerator:
    def __init__(self):
        # Prepare styles and directories
        self.styles = getSampleStyleSheet()
        os.makedirs(REPORT_DIR, exist_ok=True)
        os.makedirs(CHART_DIR, exist_ok=True)
        # Initialize handlers
        self.conf_handler = ConfluenceHandler()
        
        # Add custom styles
        self.styles.add(ParagraphStyle(
            name='Link',
            parent=self.styles['Normal'],
            textColor='blue',
            underlineProportion=0.1,
        ))
        
        # Define page size and margins
        self.page_size = letter
        self.margins = {
            'left': 0.75*inch,
            'right': 0.75*inch,
            'top': 1*inch,
            'bottom': 1*inch
        }

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

    def _make_image(self, path, max_w=6*inch, max_h=4*inch):
        """Create an Image object with preserved aspect ratio"""
        img_reader = utils.ImageReader(path)
        iw, ih = img_reader.getSize()
        ratio = min(max_w/iw, max_h/ih)
        return Image(path, width=iw*ratio, height=ih*ratio)

    def _create_list_item(self, text, style=None):
        """Create a ListItem with proper styling"""
        if style is None:
            style = self.styles['Normal']
        return ListItem(Paragraph(text, style), bulletColor='black')

    def generate_report(self, jira_handler: JiraHandler, legacy_dir: str) -> str:
        """Generate the complete report as a PDF and return its path."""
        # Fetch data via API
        df = jira_handler.get_all_tickets()

        # Build PDF
        week_number = datetime.now().isocalendar()[1] - 1
        report_path = os.path.join(REPORT_DIR, f'weekly_report_w{week_number}.pdf')
        doc = SimpleDocTemplate(
            report_path,
            pagesize=self.page_size,
            leftMargin=self.margins['left'],
            rightMargin=self.margins['right'],
            topMargin=self.margins['top'],
            bottomMargin=self.margins['bottom']
        )
        story = []

        # Title and Executive Summary (kept together)
        title_style = ParagraphStyle(
            'Title', parent=self.styles['Heading1'], fontSize=24, spaceAfter=20
        )
        story.append(KeepTogether([
            Paragraph(f"{REPORT_TITLE} - Week {week_number}", title_style),
            Spacer(1, 12),
            Paragraph("<b>Executive Summary</b>", self.styles['Heading2']),
            Paragraph(
                f"Total Tickets: {len(df)}<br/>"
                f"P1 Tickets: {len(df[df['priority'] == 'P1'])}<br/>"
                f"Cancelled/Resolved: {df['status'].str.lower().isin(['cancelled', 'closed', 'resolved']).sum()}",
                self.styles['Normal']
            ),
            Spacer(1, 12)
        ]))

        # Add Priority Changes section
        story.append(KeepTogether([
            Paragraph("Priority Changes", self.styles['Heading2']),
            Spacer(1, 6)
        ]))
        
        # Generate and add priority changes visualization
        priority_history = jira_handler.get_priority_history()
        priority_changes_path = plot_priority_changes(priority_history)
        story.append(KeepTogether([
            self._make_image(priority_changes_path),
            Spacer(1, 12)
        ]))

        # Post Mortems section
        pm = self.conf_handler.get_recent_postmortems()
        story.append(KeepTogether([
            Paragraph("P1 — Post Mortems", self.styles['Heading2']),
            Spacer(1, 6)
        ]))
        if not pm:
            story.append(Paragraph("No Post Mortems created in the last week.", self.styles['Normal']))
        else:
            items = []
            for item in pm:
                items.append(self._create_list_item(
                    f'<link href="{item["link"]}">{item["title"]}</link> ({item["created"][:10]})',
                    self.styles['Link']
                ))
            story.append(ListFlowable(items, bulletType='bullet', start='-'))
        story.append(Spacer(1, 12))

        # ISD Board Initial Troubleshooting
        total, untriaged, percent = jira_handler.get_initial_troubleshooting_metrics()
        story.append(KeepTogether([
            Paragraph("ISD Board Initial Troubleshooting", self.styles['Heading2']),
            Spacer(1, 6)
        ]))
        
        # Create donut chart
        labels = ['Triaged', 'Untriaged']
        values = [total - untriaged, untriaged]
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops={'width':0.3})
        ax.axis('equal')
        chart_path = os.path.join(CHART_DIR, 'isd_initial_troubleshooting.png')
        fig.savefig(chart_path, bbox_inches='tight')
        plt.close(fig)
        
        # Add chart and metrics
        story.append(KeepTogether([
            self._make_image(chart_path),
            Paragraph(
                f"✅ Initial triaging: {percent:.1f}%  "
                f"({total - untriaged} of {total} tickets triaged)",
                self.styles['Normal']
            ),
            Spacer(1, 12)
        ]))

        # Alerts by cluster
        counts = jira_handler.get_cluster_alert_counts()
        series = pd.Series(counts)
        fig, ax = plt.subplots(figsize=(8, 4))
        series.plot.bar(ax=ax)
        ax.set_title('Alerts by cluster')
        ax.set_xlabel('')
        ax.set_ylabel('Count')
        plt.xticks(rotation=30, ha='right')
        fig.tight_layout()
        chart_path = os.path.join(CHART_DIR, 'alerts_by_cluster.png')
        fig.savefig(chart_path, bbox_inches='tight')
        plt.close(fig)

        story.append(KeepTogether([
            Paragraph("Alerts by Cluster", self.styles['Heading2']),
            Spacer(1, 6),
            self._make_image(chart_path),
            Spacer(1, 12)
        ]))

        # Alerts by namespace
        namespace_counts = jira_handler.get_namespace_alert_counts()
        ns_series = pd.Series(namespace_counts)
        fig, ax = plt.subplots(figsize=(8, 4))
        ns_series.plot.bar(ax=ax)
        ax.set_title('Alerts by Namespace')
        ax.set_xlabel('')
        ax.set_ylabel('Count')
        plt.xticks(rotation=30, ha='right')
        fig.tight_layout()
        ns_chart = os.path.join(CHART_DIR, 'alerts_by_namespace.png')
        fig.savefig(ns_chart, bbox_inches='tight')
        plt.close(fig)

        story.append(KeepTogether([
            Paragraph("Alerts by Namespace", self.styles['Heading2']),
            Spacer(1, 6),
            self._make_image(ns_chart),
            Spacer(1, 12)
        ]))

        # Wiz Alerts, AWS GuardDuty, Snyk
        src_counts = jira_handler.get_source_alert_counts()
        series = pd.Series(src_counts)
        fig, ax = plt.subplots(figsize=(6, 3))
        series.plot.bar(ax=ax, color=['#4C72B0', '#55A868', '#C44E52'])
        ax.set_title('Wiz Alerts, AWS GuardDuty, Snyk')
        ax.set_xlabel('')
        ax.set_ylabel('Count')
        plt.xticks(rotation=0)
        fig.tight_layout()
        chart_path = os.path.join(CHART_DIR, 'alerts_by_source.png')
        fig.savefig(chart_path, bbox_inches='tight')
        plt.close(fig)

        story.append(KeepTogether([
            Paragraph("Wiz Alerts, AWS GuardDuty, Snyk", self.styles['Heading2']),
            Spacer(1, 6),
            self._make_image(chart_path),
            Spacer(1, 12)
        ]))

        # Legacy visualizations
        story.append(KeepTogether([
            Paragraph("Legacy Visualizations", self.styles['Heading1']),
            Spacer(1, 12)
        ]))

        artifacts_dir = os.path.join(legacy_dir, 'artifacts')
        title_mapping = {
            'priority_distribution.png': 'Priority Distribution',
            'cluster_distribution.png': 'Cluster Distribution',
            'namespace_distribution.png': 'Namespace Distribution',
            'weekly_trend.png': 'Weekly Trend',
            'p1_alerts.png': 'P1 Alerts'
        }

        # Add alerts_by_type_priority.png first if it exists
        priority_chart = os.path.join(artifacts_dir, 'alerts_by_type_priority.png')
        if os.path.exists(priority_chart):
            story.append(KeepTogether([
                Paragraph("Number of Alerts by Types and Priorities", self.styles['Heading2']),
                Spacer(1, 6),
                self._make_image(priority_chart),
                Spacer(1, 12)
            ]))

        # Add other PNG files
        png_files = sorted(glob.glob(os.path.join(artifacts_dir, '*.png')))
        for img_path in png_files:
            filename = os.path.basename(img_path)
            if filename == 'alerts_by_type_priority.png':
                continue
            
            title = title_mapping.get(filename, filename.replace('.png', '').replace('_', ' ').title())
            story.append(KeepTogether([
                Paragraph(title, self.styles['Heading2']),
                Spacer(1, 6),
                self._make_image(img_path),
                Spacer(1, 12)
            ]))

        # Ticket Lists
        story.append(KeepTogether([
            Paragraph("Ticket Lists", self.styles['Heading1']),
            Spacer(1, 12)
        ]))

        # 1. Duplicate list
        story.append(Paragraph("Duplicate List", self.styles['Heading2']))
        duplicate_tickets = df[df['assignee'].str.lower().str.contains('oleg.*kolomiets', na=False)]
        if not duplicate_tickets.empty:
            items = []
            for _, ticket in duplicate_tickets.iterrows():
                summary = ticket['summary']
                if len(summary) > 80:
                    summary = summary[:77] + '...'
                items.append(self._create_list_item(f"{ticket['key']}: {summary}"))
            story.append(ListFlowable(items, bulletType='bullet', start='-'))
        else:
            story.append(Paragraph("No duplicate tickets found.", self.styles['Normal']))
        story.append(Spacer(1, 12))

        # 2. Canceled list
        story.append(Paragraph("Canceled List", self.styles['Heading2']))
        canceled_tickets = df[
            (df['status'].str.lower() == 'canceled') & 
            (~df['assignee'].str.lower().str.contains('oleg.*kolomiets', na=False))
        ]
        if not canceled_tickets.empty:
            items = []
            for _, ticket in canceled_tickets.iterrows():
                summary = ticket['summary']
                if len(summary) > 80:
                    summary = summary[:77] + '...'
                reason = ticket['resolution'] if pd.notna(ticket['resolution']) else 'No reason provided'
                items.append(self._create_list_item(f"{ticket['key']}: {summary} ({reason})"))
            story.append(ListFlowable(items, bulletType='bullet', start='-'))
        else:
            story.append(Paragraph("No canceled tickets found.", self.styles['Normal']))
        story.append(Spacer(1, 12))

        # 3. Other cancelations
        story.append(Paragraph("Other Cancelations", self.styles['Heading2']))
        other_tickets = df[df['assignee'].str.lower().str.contains('arthur.*holubov', na=False)]
        if not other_tickets.empty:
            items = []
            for _, ticket in other_tickets.iterrows():
                summary = ticket['summary']
                if len(summary) > 80:
                    summary = summary[:77] + '...'
                if 'snyk' in summary.lower():
                    reason = 'non-infra'
                else:
                    reason = ticket['resolution'] if pd.notna(ticket['resolution']) else 'No reason provided'
                items.append(self._create_list_item(f"{ticket['key']}: {summary} ({reason})"))
            story.append(ListFlowable(items, bulletType='bullet', start='-'))
        else:
            story.append(Paragraph("No other cancelations found.", self.styles['Normal']))
        story.append(Spacer(1, 12))

        # Build the PDF
        doc.build(story)
        return report_path
