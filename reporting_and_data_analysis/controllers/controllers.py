# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, content_disposition
import logging

_logger = logging.getLogger(__name__)


class MedicalReportPDFController(http.Controller):
    @http.route(['/report/medical_pdf/<int:report_id>'], type='http', auth="user")
    def get_medical_report_pdf(self, report_id, **kwargs):
        """Generate PDF report for medical reports using ReportLab"""
        try:
            # Check if the report model exists
            report_model_name = 'report.med_report_pdf'  # Updated shorter name
            if report_model_name not in request.env:
                _logger.error(f"Report model {report_model_name} not found")
                return self._return_error_response("Report model not found in the system")

            # Get the report handler model
            report_model = request.env[report_model_name]

            # Get the medical report record
            medical_report = request.env['hospital.medical.report'].browse(report_id)

            if not medical_report.exists():
                return request.not_found()

            # Generate PDF using the report handler
            pdf_content = report_model._get_pdf(medical_report)

            if not pdf_content:
                return self._return_error_response("Failed to generate PDF content")

            # Set the appropriate headers for a PDF download
            filename = f"medical_report_{report_id}.pdf"
            headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', content_disposition(filename))
            ]

            # Return the PDF as a response
            return request.make_response(pdf_content, headers=headers)

        except Exception as e:
            _logger.error(f"Error generating medical report PDF: {e}")
            return self._return_error_response(f"Error generating PDF: {e}")

    def _return_error_response(self, message):
        """Return a simple error response"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error</h1>
            <p>{message}</p>
            <p>Please contact your administrator.</p>
        </body>
        </html>
        """
        return request.make_response(html, headers=[('Content-Type', 'text/html')])