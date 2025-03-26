# -*- coding: utf-8 -*-
import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from odoo import models, api, modules
import base64
import logging

_logger = logging.getLogger(__name__)


class MedicalReportPDFHandler(models.AbstractModel):
    _name = 'report.med_report_pdf'  # Shortened name
    _description = 'Báo cáo y tế sử dụng Reportlab'

    def _register_fonts(self):
        """Register fonts or use defaults if unavailable"""
        # Always use Helvetica as a safe default
        try:
            # Use Helvetica (built into ReportLab) as our default font
            pdfmetrics.registerFontFamily('Arial',
                                          normal='Helvetica', bold='Helvetica-Bold',
                                          italic='Helvetica-Oblique', boldItalic='Helvetica-BoldOblique')

        except Exception as e:
            _logger.warning(f"Font registration error: {e}")

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'hospital.medical.report',
            'docs': self.env['hospital.medical.report'].browse(docids),
        }

    def _get_pdf(self, report):
        # Register font
        self._register_fonts()

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1 * cm,
            leftMargin=1 * cm,
            topMargin=1 * cm,
            bottomMargin=1 * cm
        )

        elements = []

        # Create styles with Helvetica font
        title_style = ParagraphStyle(
            'Title',
            fontName='Helvetica-Bold',  # Use Helvetica instead of Arial
            fontSize=16,
            alignment=1,
            spaceAfter=12
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontName='Helvetica',  # Use Helvetica instead of Arial
            fontSize=14,
            spaceAfter=6
        )
        header_style = ParagraphStyle(
            'Header',
            fontName='Helvetica-Bold',  # Use Helvetica instead of Arial
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'Normal',
            fontName='Helvetica',  # Use Helvetica instead of Arial
            fontSize=10
        )

        # Add report title
        title = Paragraph(report.name if report.name else "Medical Report", title_style)
        elements.append(title)

        # Add date range
        if report.date_from and report.date_to:
            date_info = Paragraph(
                f"Từ ngày: {report.date_from.strftime('%d/%m/%Y')} đến ngày: {report.date_to.strftime('%d/%m/%Y')}",
                subtitle_style
            )
            elements.append(date_info)
            elements.append(Spacer(1, 0.5 * cm))

        # Add basic content
        elements.append(Paragraph("Báo cáo y tế", header_style))
        if report.report_type:
            elements.append(Paragraph(f"Loại báo cáo: {report.report_type}", normal_style))

        # Add report text content
        if report.report_data:
            elements.append(Paragraph("Nội dung báo cáo:", header_style))
            elements.append(Paragraph(report.report_data, normal_style))

        # Try to add charts only if successful
        try:
            if report.chart_image:
                elements.append(Spacer(1, 0.5 * cm))
                elements.append(Paragraph("Biểu đồ:", header_style))

                chart_data = base64.b64decode(report.chart_image)
                chart_io = io.BytesIO(chart_data)
                chart_image = Image(chart_io)

                # Set reasonable width
                max_width = 450
                chart_image.drawWidth = max_width
                chart_image.drawHeight = chart_image.drawHeight * (max_width / chart_image.drawWidth)

                elements.append(chart_image)
        except Exception as e:
            _logger.error(f"Error adding chart: {e}")
            elements.append(Paragraph("Không thể hiển thị biểu đồ", normal_style))

        elements.append(Spacer(1, 1 * cm))

        # Add footer
        footer_text = Paragraph(
            f"Báo cáo được tạo vào ngày {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            ParagraphStyle('Footer', fontName='Helvetica-Oblique', fontSize=8)
        )
        elements.append(footer_text)

        try:
            # Build PDF
            doc.build(elements)

            # Get buffer content
            pdf = buffer.getvalue()
            buffer.close()

            return pdf
        except Exception as e:
            _logger.error(f"Error building PDF: {e}")

            # Create a very simple error PDF
            error_buffer = io.BytesIO()
            error_doc = SimpleDocTemplate(
                error_buffer,
                pagesize=A4,
                rightMargin=1 * cm,
                leftMargin=1 * cm,
                topMargin=1 * cm,
                bottomMargin=1 * cm
            )

            error_elements = []
            error_elements.append(Paragraph("Error Report", title_style))
            error_elements.append(Paragraph(f"Error: {str(e)}", normal_style))

            try:
                error_doc.build(error_elements)
                error_pdf = error_buffer.getvalue()
                error_buffer.close()
                return error_pdf
            except:
                # If even this fails, return a minimal PDF
                return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>endobj 4 0 obj<</Length 25>>stream\nBT /F1 12 Tf 100 700 Td (Error generating report) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n286\n%%EOF"