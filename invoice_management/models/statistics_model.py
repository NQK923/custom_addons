from odoo import models, fields, api
from datetime import datetime, timedelta
import calendar
import json


class ClinicStatistics(models.Model):
    _name = 'clinic.statistics'
    _description = 'Thống kê phòng khám'

    name = fields.Char(string='Tên', readonly=True)
    date_from = fields.Date(string='Từ ngày')
    date_to = fields.Date(string='Đến ngày')

    # Thống kê doanh thu
    total_revenue = fields.Float(string='Tổng doanh thu', readonly=True)
    service_revenue = fields.Float(string='Doanh thu dịch vụ', readonly=True)
    medicine_revenue = fields.Float(string='Doanh thu thuốc', readonly=True)
    insurance_revenue = fields.Float(string='Doanh thu từ bảo hiểm', readonly=True)
    patient_revenue = fields.Float(string='Doanh thu từ bệnh nhân', readonly=True)

    # Thống kê đơn hàng
    total_invoices = fields.Integer(string='Tổng số hóa đơn', readonly=True)
    paid_invoices = fields.Integer(string='Hóa đơn đã thanh toán', readonly=True)
    cancelled_invoices = fields.Integer(string='Hóa đơn đã hủy', readonly=True)

    # Thống kê dịch vụ
    most_used_service_id = fields.Many2one('clinic.service', string='Dịch vụ được sử dụng nhiều nhất', readonly=True)
    most_used_service_count = fields.Integer(string='Số lượt sử dụng', readonly=True)

    # Thống kê thuốc
    most_sold_product_id = fields.Many2one('pharmacy.product', string='Thuốc bán chạy nhất', readonly=True)
    most_sold_product_count = fields.Integer(string='Số lượng bán', readonly=True)

    # Dữ liệu biểu đồ
    chart_data = fields.Text(string='Dữ liệu biểu đồ', readonly=True)

    # Thống kê theo ngày
    daily_stats_ids = fields.One2many('clinic.statistics.daily', 'statistics_id', string='Thống kê theo ngày')

    @api.model
    def create_statistics(self, date_from, date_to):
        """Tạo thống kê từ dữ liệu hóa đơn trong khoảng thời gian"""
        # Tính toán thống kê
        name = f'Thống kê từ {date_from} đến {date_to}'

        # Tìm tất cả hóa đơn trong khoảng thời gian
        domain = [
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to)
        ]
        invoices = self.env['clinic.invoice'].search(domain)

        # Tính tổng doanh thu
        total_revenue = 0
        service_revenue = 0
        medicine_revenue = 0
        insurance_revenue = 0
        patient_revenue = 0

        # Đếm số lượng hóa đơn
        total_invoices = len(invoices)
        paid_invoices = len(invoices.filtered(lambda x: x.state == 'paid'))
        cancelled_invoices = len(invoices.filtered(lambda x: x.state == 'cancelled'))

        # Tính tổng doanh thu (chỉ từ hóa đơn đã thanh toán)
        paid_invoices_records = invoices.filtered(lambda x: x.state == 'paid')
        for invoice in paid_invoices_records:
            total_revenue += invoice.amount_total
            service_revenue += invoice.service_amount
            medicine_revenue += invoice.medicine_amount
            insurance_revenue += invoice.insurance_amount
            patient_revenue += invoice.patient_amount

        # Tìm dịch vụ được sử dụng nhiều nhất
        service_counts = {}
        for invoice in paid_invoices_records:
            for line in invoice.service_lines:
                service_id = line.service_id.id
                if service_id not in service_counts:
                    service_counts[service_id] = 0
                service_counts[service_id] += line.quantity

        most_used_service_id = False
        most_used_service_count = 0
        if service_counts:
            most_used_service_id = max(service_counts, key=service_counts.get)
            most_used_service_count = service_counts[most_used_service_id]

        # Tìm thuốc bán chạy nhất
        product_counts = {}
        for invoice in paid_invoices_records:
            for line in invoice.product_lines:
                product_id = line.product_id.id
                if product_id not in product_counts:
                    product_counts[product_id] = 0
                product_counts[product_id] += line.quantity

        most_sold_product_id = False
        most_sold_product_count = 0
        if product_counts:
            most_sold_product_id = max(product_counts, key=product_counts.get)
            most_sold_product_count = product_counts[most_sold_product_id]

        daily_stats = []
        delta = timedelta(days=1)
        current_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()

        while current_date <= end_date:
            daily_invoices = invoices.filtered(lambda x: x.invoice_date == current_date and x.state == 'paid')

            daily_total = sum(inv.amount_total for inv in daily_invoices)
            daily_service = sum(inv.service_amount for inv in daily_invoices)
            daily_medicine = sum(inv.medicine_amount for inv in daily_invoices)

            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total': daily_total,
                'service': daily_service,
                'medicine': daily_medicine,
                'count': len(daily_invoices)
            })

            current_date += delta

        # Tạo bản ghi thống kê
        vals = {
            'name': name,
            'date_from': date_from,
            'date_to': date_to,
            'total_revenue': total_revenue,
            'service_revenue': service_revenue,
            'medicine_revenue': medicine_revenue,
            'insurance_revenue': insurance_revenue,
            'patient_revenue': patient_revenue,
            'total_invoices': total_invoices,
            'paid_invoices': paid_invoices,
            'cancelled_invoices': cancelled_invoices,
            'most_used_service_id': most_used_service_id,
            'most_used_service_count': most_used_service_count,
            'most_sold_product_id': most_sold_product_id,
            'most_sold_product_count': most_sold_product_count,
            'daily_stats_ids': [(0, 0, {
                'date': stat['date'],
                'total_revenue': stat['total'],
                'service_revenue': stat['service'],
                'medicine_revenue': stat['medicine'],
                'invoice_count': stat['count']
            }) for stat in daily_stats]
        }

        return self.create(vals)

    def generate_monthly_report(self):
        """Tạo báo cáo thống kê theo tháng"""
        # Lấy tháng hiện tại
        today = fields.Date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        # Tạo thống kê
        return self.create_statistics(first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d'))

    def action_view_form(self):
        """Return action to view the statistics form"""
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.statistics',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }


class ClinicStatisticsDaily(models.Model):
    _name = 'clinic.statistics.daily'
    _description = 'Thống kê theo ngày'

    statistics_id = fields.Many2one('clinic.statistics', string='Thống kê', ondelete='cascade')
    date = fields.Date(string='Ngày', required=True)
    total_revenue = fields.Float(string='Tổng doanh thu')
    service_revenue = fields.Float(string='Doanh thu dịch vụ')
    medicine_revenue = fields.Float(string='Doanh thu thuốc')
    invoice_count = fields.Integer(string='Số hóa đơn')


class ClinicStatisticsWizard(models.TransientModel):
    _name = 'clinic.statistics.wizard'
    _description = 'Wizard tạo thống kê'

    date_from = fields.Date(string='Từ ngày', required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='Đến ngày', required=True, default=lambda self: fields.Date.today())

    def action_generate_statistics(self):
        """Tạo thống kê và xuất file PDF"""
        self.ensure_one()

        # Kiểm tra ngày hợp lệ
        if self.date_from > self.date_to:
            raise models.ValidationError('Ngày bắt đầu phải nhỏ hơn ngày kết thúc')

        statistics = self.env['clinic.statistics'].create_statistics(
            self.date_from.strftime('%Y-%m-%d'),
            self.date_to.strftime('%Y-%m-%d')
        )

        return self.env.ref('invoice_management.action_report_statistics_reportlab').report_action(statistics)