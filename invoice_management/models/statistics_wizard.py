from odoo import models, fields, api
from datetime import datetime, timedelta


class ClinicStatisticsWizard(models.TransientModel):
    _name = 'clinic.statistics.wizard'
    _description = 'Wizard để tạo báo cáo thống kê'

    date_from = fields.Date(string='Từ ngày', default=lambda self: fields.Date.today() - timedelta(days=30),
                            required=True)
    date_to = fields.Date(string='Đến ngày', default=fields.Date.today, required=True)
    report_type = fields.Selection([
        ('invoice', 'Hóa đơn'),
        ('service', 'Dịch vụ'),
        ('product', 'Thuốc'),
        ('insurance', 'Bảo hiểm'),
        ('purchase', 'Nhập hàng'),
        ('summary', 'Tổng hợp')
    ], string='Loại báo cáo', default='summary', required=True)

    def action_generate_report(self):
        stats = self.env['clinic.statistics']

        # Lấy thống kê theo loại báo cáo được chọn
        if self.report_type == 'invoice':
            data = stats.get_invoice_statistics(self.date_from, self.date_to)
        elif self.report_type == 'service':
            data = stats.get_service_statistics(self.date_from, self.date_to)
        elif self.report_type == 'product':
            data = stats.get_product_statistics(self.date_from, self.date_to)
        elif self.report_type == 'insurance':
            data = stats.get_insurance_statistics(self.date_from, self.date_to)
        elif self.report_type == 'purchase':
            data = stats.get_purchase_statistics(self.date_from, self.date_to)
        else:  # summary
            data = {
                'invoice': stats.get_invoice_statistics(self.date_from, self.date_to),
                'service': stats.get_service_statistics(self.date_from, self.date_to),
                'product': stats.get_product_statistics(self.date_from, self.date_to),
                'insurance': stats.get_insurance_statistics(self.date_from, self.date_to),
                'purchase': stats.get_purchase_statistics(self.date_from, self.date_to)
            }

        # Tạo report context
        context = {
            'data': data,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'report_type': self.report_type
        }

        return {
            'name': 'Báo cáo thống kê',
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.statistics',
            'view_mode': 'form',
            'target': 'current',
            'context': context,
        }