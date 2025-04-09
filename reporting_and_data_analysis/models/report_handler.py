# -*- coding: utf-8 -*-
import base64
import io
import logging
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Frame, PageTemplate, Flowable
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether

from odoo import models, api

_logger = logging.getLogger(__name__)


class VerticalText(Flowable):
    """Custom Flowable for vertical text in the sidebar"""

    def __init__(self, text, font_name='Arial', font_size=8, color=colors.gray):
        Flowable.__init__(self)
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self.color = color

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFont(self.font_name, self.font_size)
        canvas.setFillColor(self.color)
        canvas.rotate(90)
        canvas.drawString(0, -2 * mm, self.text)
        canvas.restoreState()


class MedicalReportPDFHandler(models.AbstractModel):
    _name = 'report.med_report_pdf'
    _description = 'Báo cáo y tế sử dụng Reportlab'

    def _register_fonts(self):
        """Register Arial fonts for Vietnamese character support"""
        try:
            # Register Arial fonts for better Vietnamese character support
            pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'Arialbd.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Italic', 'Ariali.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-BoldItalic', 'Arialbi.ttf'))

            pdfmetrics.registerFontFamily('Arial',
                                          normal='Arial', bold='Arial-Bold',
                                          italic='Arial-Italic', boldItalic='Arial-BoldItalic')

        except Exception as e:
            _logger.warning(f"Arial font registration error: {e}")
            _logger.warning("Falling back to Helvetica (Vietnamese characters may not display correctly)")
            # If Arial registration fails, fall back to built-in Helvetica
            try:
                pdfmetrics.registerFontFamily('Arial',
                                              normal='Helvetica', bold='Helvetica-Bold',
                                              italic='Helvetica-Oblique', boldItalic='Helvetica-BoldOblique')
            except Exception as fallback_error:
                _logger.error(f"Font fallback registration error: {fallback_error}")

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'hospital.medical.report',
            'docs': self.env['hospital.medical.report'].browse(docids),
        }

    def _get_company_info(self):
        """Get company information for the report header"""
        company = self.env.company
        return {
            'name': company.name or 'Healthcare Center',
            'street': company.street or '',
            'city': company.city or '',
            'phone': company.phone or '',
            'email': company.email or '',
            'website': company.website or '',
            'logo': company.logo or False
        }

    def _extract_report_data(self, report_text):
        """Extract structured data from report text"""
        # This function parses the report data text into a structured format
        # for better presentation in tables

        if not report_text:
            return [], []

        lines = report_text.strip().split('\n')
        headers = []
        data_sections = []
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.endswith(':'):  # This is a header
                headers.append(line.strip(':'))
                current_section = []
                data_sections.append(current_section)
            elif line.startswith('-') or line.startswith('•'):  # This is a list item
                if current_section is not None:
                    current_section.append(line.lstrip('- •'))

        return headers, data_sections

    def _create_header_footer(self, canvas, doc, report, company_info):
        """Add header and footer to each page"""
        canvas.saveState()

        # Header with company info and report title
        # Draw blue header bar
        canvas.setFillColor(colors.lightblue)
        canvas.rect(0, doc.height + doc.topMargin - 0.5 * cm,
                    doc.width + doc.leftMargin + doc.rightMargin, 2.5 * cm, fill=True, stroke=False)

        # Company logo (if available)
        if company_info.get('logo'):
            try:
                logo_data = base64.b64decode(company_info['logo'])
                logo_io = io.BytesIO(logo_data)
                canvas.drawImage(logo_io, doc.leftMargin, doc.height + doc.topMargin + 0.5 * cm,
                                 width=2 * cm, height=1.5 * cm, preserveAspectRatio=True)
            except Exception as e:
                _logger.error(f"Error displaying logo: {e}")

        # Company name and info
        canvas.setFillColor(colors.white)
        canvas.setFont('Arial-Bold', 12)
        canvas.drawString(doc.leftMargin + 2.5 * cm, doc.height + doc.topMargin + 1.5 * cm,
                          company_info.get('name', 'Healthcare Center'))

        canvas.setFont('Arial', 8)
        address = f"{company_info.get('street', '')} {company_info.get('city', '')}"
        canvas.drawString(doc.leftMargin + 2.5 * cm, doc.height + doc.topMargin + 1.1 * cm, address)

        contact = f"Tel: {company_info.get('phone', '')} | Email: {company_info.get('email', '')}"
        canvas.drawString(doc.leftMargin + 2.5 * cm, doc.height + doc.topMargin + 0.7 * cm, contact)

        # Report title on right side
        canvas.setFont('Arial-Bold', 14)
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin + 1.1 * cm,
                               report.name if report.name else "Medical Report")

        # Print date range
        if report.date_from and report.date_to:
            date_info = f"Thời gian: {report.date_from.strftime('%d/%m/%Y')} - {report.date_to.strftime('%d/%m/%Y')}"
            canvas.setFont('Arial', 10)
            canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin + 0.7 * cm, date_info)

        # Footer
        canvas.setFillColor(colors.darkblue)
        canvas.rect(0, 0, doc.width + doc.leftMargin + doc.rightMargin, 1 * cm, fill=True, stroke=False)

        # Add page number
        canvas.setFillColor(colors.white)
        canvas.setFont('Arial', 8)
        page_num = f"Trang {doc.page} / {doc.page}"  # This will be updated when all pages are rendered
        canvas.drawRightString(doc.width + doc.leftMargin - 0.5 * cm, 0.5 * cm, page_num)

        # Add timestamp
        timestamp = f"Tạo báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        canvas.drawString(doc.leftMargin + 0.5 * cm, 0.5 * cm, timestamp)

        # Side ribbon/banner
        canvas.setFillColor(colors.darkblue)
        canvas.rect(0, 0, 0.5 * cm, doc.height + doc.topMargin + doc.bottomMargin, fill=True, stroke=False)

        # Add vertical text to the ribbon
        canvas.saveState()
        canvas.setFillColor(colors.white)
        canvas.setFont('Arial', 8)
        canvas.rotate(90)
        canvas.drawString(2 * cm, -0.3 * cm, "BÁO CÁO Y TẾ | HEALTHCARE REPORT")
        canvas.restoreState()

        canvas.restoreState()

    def _get_pdf(self, report):
        # Register font
        self._register_fonts()

        # Get company info
        company_info = self._get_company_info()

        # Create a BytesIO buffer for the PDF
        buffer = io.BytesIO()

        # Create the PDF document with custom header/footer
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=3 * cm,
            bottomMargin=1.5 * cm
        )

        # Create a frame template with the callback function
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='normal'
        )

        # Create a page template with the callback function
        header_footer_callback = lambda canvas, doc: self._create_header_footer(canvas, doc, report, company_info)
        template = PageTemplate(id='medical_report', frames=[frame], onPage=header_footer_callback)
        doc.addPageTemplates([template])

        # Create styles with improved typography
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontName='Arial-Bold',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.darkblue
        )

        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontName='Arial-Bold',
            fontSize=14,
            leading=18,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.darkblue,
            borderWidth=0,
            borderPadding=5,
            borderColor=colors.lightblue,
            backColor=colors.lightblue.clone(alpha=0.2)
        )

        subsection_style = ParagraphStyle(
            'Subsection',
            parent=styles['Heading3'],
            fontName='Arial-Bold',
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.darkblue
        )

        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontName='Arial',
            fontSize=10,
            leading=14,
            spaceBefore=4,
            spaceAfter=4
        )

        data_style = ParagraphStyle(
            'DataText',
            parent=styles['Normal'],
            fontName='Arial',
            fontSize=9,
            leading=12
        )

        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName='Arial-Italic',
            fontSize=8,
            textColor=colors.gray
        )

        # Start building the document
        elements = []

        # Add main report content
        if report.report_type:
            report_type_map = {
                'patient': 'Tình hình bệnh nhân',
                'epidemiology': 'Dịch tễ học',
                'service_quality': 'Chất lượng dịch vụ'
            }
            report_type_name = report_type_map.get(report.report_type, report.report_type)
            elements.append(Paragraph(f"BÁO CÁO {report_type_name.upper()}", title_style))

        # Process report content
        if report.report_data:
            # Try to extract structured data
            headers, data_sections = self._extract_report_data(report.report_data)

            # If we have parsed data, display in a nicer format
            if headers and all(len(section) > 0 for section in data_sections):
                for i, (header, section_data) in enumerate(zip(headers, data_sections)):
                    elements.append(Paragraph(header, section_title_style))

                    # Create a table for the section data
                    table_data = []
                    for item in section_data:
                        if ":" in item:
                            key, value = item.split(":", 1)
                            table_data.append([
                                Paragraph(key.strip(), normal_style),
                                Paragraph(value.strip(), normal_style)
                            ])
                        else:
                            table_data.append([
                                Paragraph("•", normal_style),
                                Paragraph(item.strip(), normal_style)
                            ])

                    if table_data:
                        # Create table with better styling
                        col_widths = [doc.width * 0.3, doc.width * 0.7]
                        table = Table(table_data, colWidths=col_widths)
                        table.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue.clone(alpha=0.1)),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                            ('BOX', (0, 0), (-1, -1), 0.5, colors.darkblue),
                            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.whitesmoke])
                        ]))
                        elements.append(table)

                    elements.append(Spacer(1, 0.5 * cm))
            else:
                # Just use the raw text with some formatting
                lines = report.report_data.strip().split('\n')
                current_section = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        elements.append(Spacer(1, 0.2 * cm))
                    elif line.isupper() or line.endswith(':'):
                        # This is likely a section header
                        elements.append(Paragraph(line, section_title_style))
                    elif line.startswith('-') or line.startswith('•'):
                        # This is a list item
                        elements.append(Paragraph(line, normal_style))
                    else:
                        # Regular text
                        elements.append(Paragraph(line, normal_style))

        # Add charts section
        if report.chart_image or report.additional_chart1 or report.additional_chart2:
            elements.append(PageBreak())
            elements.append(Paragraph("BIỂU ĐỒ VÀ PHÂN TÍCH TRỰC QUAN", title_style))

            # Process and add the main chart
            if report.chart_image:
                elements.append(Paragraph("Biểu đồ chính", section_title_style))

                try:
                    chart_data = base64.b64decode(report.chart_image)
                    chart_io = io.BytesIO(chart_data)
                    chart_image = Image(chart_io)

                    # Size the chart appropriately
                    max_width = doc.width
                    max_height = 10 * cm
                    chart_image.drawWidth = min(max_width, chart_image.drawWidth)
                    chart_image.drawHeight = min(max_height,
                                                 chart_image.drawHeight * (max_width / chart_image.drawWidth))

                    # Center the image and add some space around it
                    chart_container = []
                    chart_container.append(Spacer(1, 0.5 * cm))
                    chart_container.append(chart_image)
                    chart_container.append(Spacer(1, 0.5 * cm))

                    elements.append(KeepTogether(chart_container))

                except Exception as e:
                    _logger.error(f"Error adding chart: {e}")
                    elements.append(Paragraph("Không thể hiển thị biểu đồ chính", normal_style))

            # Add additional charts
            if report.additional_chart1:
                elements.append(Paragraph("Biểu đồ bổ sung 1", section_title_style))

                try:
                    chart_data = base64.b64decode(report.additional_chart1)
                    chart_io = io.BytesIO(chart_data)
                    chart_image = Image(chart_io)

                    # Size the chart appropriately
                    max_width = doc.width
                    max_height = 10 * cm
                    chart_image.drawWidth = min(max_width, chart_image.drawWidth)
                    chart_image.drawHeight = min(max_height,
                                                 chart_image.drawHeight * (max_width / chart_image.drawWidth))

                    # Center the image and add some space around it
                    chart_container = []
                    chart_container.append(Spacer(1, 0.5 * cm))
                    chart_container.append(chart_image)
                    chart_container.append(Spacer(1, 0.5 * cm))

                    elements.append(KeepTogether(chart_container))

                except Exception as e:
                    _logger.error(f"Error adding additional chart 1: {e}")
                    elements.append(Paragraph("Không thể hiển thị biểu đồ bổ sung 1", normal_style))

            if report.additional_chart2:
                elements.append(Paragraph("Biểu đồ bổ sung 2", section_title_style))

                try:
                    chart_data = base64.b64decode(report.additional_chart2)
                    chart_io = io.BytesIO(chart_data)
                    chart_image = Image(chart_io)

                    # Size the chart appropriately
                    max_width = doc.width
                    max_height = 10 * cm
                    chart_image.drawWidth = min(max_width, chart_image.drawWidth)
                    chart_image.drawHeight = min(max_height,
                                                 chart_image.drawHeight * (max_width / chart_image.drawWidth))

                    # Center the image and add some space around it
                    chart_container = []
                    chart_container.append(Spacer(1, 0.5 * cm))
                    chart_container.append(chart_image)
                    chart_container.append(Spacer(1, 0.5 * cm))

                    elements.append(KeepTogether(chart_container))

                except Exception as e:
                    _logger.error(f"Error adding additional chart 2: {e}")
                    elements.append(Paragraph("Không thể hiển thị biểu đồ bổ sung 2", normal_style))

        # Add signature space at the end
        elements.append(Spacer(1, 1 * cm))
        elements.append(Paragraph("XÁC NHẬN BÁO CÁO", subsection_style))

        # Create a table for signatures
        signature_data = [
            [Paragraph("Người lập báo cáo", normal_style),
             Paragraph("Trưởng khoa/phòng", normal_style),
             Paragraph("Ban Giám đốc", normal_style)],
            ["", "", ""],
            ["", "", ""],
            ["", "", ""],
            ["", "", ""],
            [Paragraph("(Ký, ghi rõ họ tên)", data_style),
             Paragraph("(Ký, ghi rõ họ tên)", data_style),
             Paragraph("(Ký, ghi rõ họ tên)", data_style)]
        ]

        signature_table = Table(signature_data, colWidths=[doc.width / 3.0] * 3)
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 1), (0, 4)),
            ('SPAN', (1, 1), (1, 4)),
            ('SPAN', (2, 1), (2, 4)),
            ('LINEBELOW', (0, 4), (2, 4), 0.5, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 20),
        ]))

        elements.append(signature_table)

        try:
            # Build PDF
            doc.build(elements)

            # Get buffer content
            pdf = buffer.getvalue()
            buffer.close()

            return pdf
        except Exception as e:
            _logger.error(f"Error building PDF: {e}")

            # Create a better error PDF with more details
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
            error_title = Paragraph("Error Report", title_style)
            error_elements.append(error_title)

            error_elements.append(Spacer(1, 1 * cm))
            error_elements.append(Paragraph("An error occurred while generating the report:", subsection_style))
            error_elements.append(Paragraph(str(e), normal_style))

            error_elements.append(Spacer(1, 0.5 * cm))
            error_elements.append(Paragraph("Technical Details:", subsection_style))

            # Add error details in a formatted way
            error_details = [
                ["Error Type", str(type(e).__name__)],
                ["Error Message", str(e)],
                ["Report ID", str(report.id)],
                ["Report Type", str(report.report_type)],
                ["Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            ]

            error_table = Table(error_details, colWidths=[doc.width * 0.3, doc.width * 0.7])
            error_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))

            error_elements.append(error_table)

            try:
                error_doc.build(error_elements)
                error_pdf = error_buffer.getvalue()
                error_buffer.close()
                return error_pdf
            except:
                # If even this fails, return a minimal PDF
                return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>endobj 4 0 obj<</Length 25>>stream\nBT /F1 12 Tf 100 700 Td (Error generating report) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n286\n%%EOF"
