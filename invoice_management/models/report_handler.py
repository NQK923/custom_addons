import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from odoo import models, api, modules


class ClinicStatisticsReportLab(models.AbstractModel):
    _name = 'report.invoice_management.report_statistics_reportlab_template'
    _description = 'Báo cáo thống kê sử dụng Reportlab'

    def _register_fonts(self):
        """Đăng ký font Arial từ Windows để hỗ trợ tiếng Việt"""
        # Đường dẫn đến thư mục fonts của Windows
        windows_fonts_path = 'C:/Windows/Fonts'

        # Đăng ký các font Arial
        pdfmetrics.registerFont(TTFont('Arial', os.path.join(windows_fonts_path, 'arial.ttf')))
        pdfmetrics.registerFont(TTFont('Arial-Bold', os.path.join(windows_fonts_path, 'arialbd.ttf')))
        pdfmetrics.registerFont(TTFont('Arial-Italic', os.path.join(windows_fonts_path, 'ariali.ttf')))
        pdfmetrics.registerFont(TTFont('Arial-BoldItalic', os.path.join(windows_fonts_path, 'arialbi.ttf')))

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'clinic.statistics',
            'docs': self.env['clinic.statistics'].browse(docids),
        }

    def _get_pdf(self, statistics):
        # Đăng ký font
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

        # Tạo các styles với font Arial
        title_style = ParagraphStyle(
            'Title',
            fontName='Arial-Bold',
            fontSize=16,
            alignment=1,
            spaceAfter=12
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontName='Arial',
            fontSize=14,
            spaceAfter=6
        )
        header_style = ParagraphStyle(
            'Header',
            fontName='Arial-Bold',
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'Normal',
            fontName='Arial',
            fontSize=10
        )

        # Tạo các phần tử với font Arial
        title = Paragraph(statistics.name, title_style)
        elements.append(title)

        date_info = Paragraph(
            f"Từ ngày: {statistics.date_from.strftime('%d/%m/%Y')} đến ngày: {statistics.date_to.strftime('%d/%m/%Y')}",
            subtitle_style
        )
        elements.append(date_info)
        elements.append(Spacer(1, 0.5 * cm))

        overview_header = Paragraph("Tổng quan", header_style)
        elements.append(overview_header)

        overview_data = [
            ["Thông tin", "Giá trị"],
            ["Tổng số hóa đơn", str(statistics.total_invoices)],
            ["Hóa đơn đã thanh toán", str(statistics.paid_invoices)],
            ["Hóa đơn đã hủy", str(statistics.cancelled_invoices)]
        ]
        overview_table = Table(overview_data, colWidths=[10 * cm, 7 * cm])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Arial-Bold'),
            ('FONTNAME', (0, 1), (1, -1), 'Arial'),
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(overview_table)
        elements.append(Spacer(1, 0.5 * cm))

        revenue_header = Paragraph("Doanh thu", header_style)
        elements.append(revenue_header)

        def format_money(amount):
            return f"{amount:,.0f} VND"

        revenue_data = [
            ["Loại doanh thu", "Số tiền"],
            ["Tổng doanh thu", format_money(statistics.total_revenue)],
            ["Doanh thu dịch vụ", format_money(statistics.service_revenue)],
            ["Doanh thu thuốc", format_money(statistics.medicine_revenue)],
            ["Doanh thu từ bảo hiểm", format_money(statistics.insurance_revenue)],
            ["Doanh thu từ bệnh nhân", format_money(statistics.patient_revenue)]
        ]
        revenue_table = Table(revenue_data, colWidths=[10 * cm, 7 * cm])
        revenue_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Arial-Bold'),
            ('FONTNAME', (0, 1), (1, -1), 'Arial'),  # Đảm bảo nội dung bảng sử dụng Arial
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(revenue_table)
        elements.append(Spacer(1, 0.5 * cm))

        top_header = Paragraph("Top dịch vụ & thuốc", header_style)
        elements.append(top_header)

        top_data = [
            ["Danh mục", "Chi tiết", "Số lượng"],
        ]

        if statistics.most_used_service_id:
            top_data.append([
                "Dịch vụ được sử dụng nhiều nhất",
                statistics.most_used_service_id.service_name or "",
                str(statistics.most_used_service_count)
            ])
        else:
            top_data.append(["Dịch vụ được sử dụng nhiều nhất", "Không có dữ liệu", ""])

        if statistics.most_sold_product_id:
            top_data.append([
                "Thuốc bán chạy nhất",
                statistics.most_sold_product_id.name or "",
                str(statistics.most_sold_product_count)
            ])
        else:
            top_data.append(["Thuốc bán chạy nhất", "Không có dữ liệu", ""])

        top_table = Table(top_data, colWidths=[7 * cm, 7 * cm, 3 * cm])
        top_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Arial'),  # Đảm bảo nội dung bảng sử dụng Arial
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),  # Số lượng căn giữa
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(top_table)
        elements.append(Spacer(1, 0.5 * cm))

        # Thống kê theo ngày
        if statistics.daily_stats_ids:
            daily_header = Paragraph("Thống kê theo ngày", header_style)
            elements.append(daily_header)

            daily_data = [
                ["Ngày", "Số hóa đơn", "Tổng doanh thu", "Dịch vụ", "Thuốc"],
            ]

            # Tính tổng
            total_invoices = 0
            total_revenue = 0
            total_service = 0
            total_medicine = 0

            # Thêm dữ liệu từng ngày
            for day in statistics.daily_stats_ids:
                daily_data.append([
                    day.date.strftime("%d/%m/%Y"),
                    str(day.invoice_count),
                    format_money(day.total_revenue),
                    format_money(day.service_revenue),
                    format_money(day.medicine_revenue)
                ])

                total_invoices += day.invoice_count
                total_revenue += day.total_revenue
                total_service += day.service_revenue
                total_medicine += day.medicine_revenue

            # Thêm dòng tổng
            daily_data.append([
                "Tổng cộng",
                str(total_invoices),
                format_money(total_revenue),
                format_money(total_service),
                format_money(total_medicine)
            ])

            daily_table = Table(daily_data, colWidths=[3.5 * cm, 2.5 * cm, 4 * cm, 4 * cm, 4 * cm])
            daily_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Dòng tổng
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
                ('FONTNAME', (0, 1), (-1, -2), 'Arial'),  # Nội dung bảng
                ('FONTNAME', (0, -1), (-1, -1), 'Arial-Bold'),  # Dòng tổng
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Số hóa đơn căn giữa
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Các cột tiền căn phải
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(daily_table)

        # Thêm chân trang
        footer_text = Paragraph(
            f"Báo cáo được tạo vào ngày {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            ParagraphStyle('Footer', fontName='Arial-Italic', fontSize=8)
        )
        elements.append(Spacer(1, 1 * cm))
        elements.append(footer_text)

        # Tạo PDF
        doc.build(elements)

        # Lấy nội dung của buffer
        pdf = buffer.getvalue()
        buffer.close()

        return pdf

    @api.model
    def _render_qweb_pdf(self, docids, data=None):
        statistics = self.env['clinic.statistics'].browse(docids)
        pdf_content = self._get_pdf(statistics)
        return pdf_content, 'pdf'