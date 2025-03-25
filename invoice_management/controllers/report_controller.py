import json
from odoo import http
from odoo.http import request, content_disposition


class StatisticsReportController(http.Controller):
    @http.route(['/report/statistics_pdf/<int:statistics_id>'], type='http', auth="user")
    def get_statistics_pdf(self, statistics_id, **kwargs):
        """Generate PDF report directly using ReportLab"""
        # Get the report handler model
        report_model = request.env['report.invoice_management.report_statistics_reportlab_template']
        # Get the statistics record
        statistics = request.env['clinic.statistics'].browse(statistics_id)

        if not statistics.exists():
            return request.not_found()

        # Generate PDF using your existing method
        pdf_content = report_model._get_pdf(statistics)

        # Set the appropriate headers for a PDF download
        filename = f"statistics_report_{statistics_id}.pdf"
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', content_disposition(filename))
        ]

        # Return the PDF as a response
        return request.make_response(pdf_content, headers=headers)