from odoo import models, fields, api
from datetime import datetime, timedelta
import calendar


class ClinicStatistics(models.Model):
    _name = 'clinic.statistics'
    _description = 'Thống kê phòng khám'
    # Remove _auto = False to make it a regular table model instead of a view
    # This allows storing data and executing methods

    name = fields.Char(string='Tên')
    date = fields.Date(string='Ngày')
    month = fields.Char(string='Tháng')
    year = fields.Char(string='Năm')

    # Date filter fields
    date_from = fields.Date(string='Từ ngày', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='Đến ngày', default=lambda self: fields.Date.today())

    # Invoice statistics
    total_invoices = fields.Integer(string='Tổng số hóa đơn', readonly=True)
    total_amount = fields.Float(string='Tổng doanh thu', readonly=True)
    service_amount = fields.Float(string='Doanh thu dịch vụ', readonly=True)
    medicine_amount = fields.Float(string='Doanh thu thuốc', readonly=True)
    insurance_amount = fields.Float(string='Bảo hiểm chi trả', readonly=True)
    patient_amount = fields.Float(string='Bệnh nhân chi trả', readonly=True)

    # Patient statistics
    patient_count = fields.Integer(string='Số lượng bệnh nhân', readonly=True)
    new_patient_count = fields.Integer(string='Bệnh nhân mới', readonly=True)

    # Additional fields for the view
    revenue_chart = fields.Text(string='Biểu đồ doanh thu', readonly=True)
    top_services = fields.Text(string='Top dịch vụ', readonly=True)
    top_products = fields.Text(string='Top thuốc', readonly=True)
    patient_insurance_count = fields.Integer(string='Số BN có bảo hiểm', readonly=True)
    patient_without_insurance_count = fields.Integer(string='Số BN không có bảo hiểm', readonly=True)
    total_purchases = fields.Integer(string='Tổng số đơn nhập', readonly=True)
    purchase_amount = fields.Float(string='Giá trị nhập hàng', readonly=True)
    total_quantity = fields.Integer(string='Tổng số lượng', readonly=True)
    insurance_percentage = fields.Float(string='Tỷ lệ bảo hiểm', readonly=True)

    # Add method to calculate statistics on button click
    def action_calculate_statistics(self):
        for record in self:
            # Get invoice statistics
            invoice_stats = self.get_invoice_statistics(record.date_from, record.date_to)
            record.total_invoices = invoice_stats['total_invoices']
            record.total_amount = invoice_stats['total_amount']
            record.service_amount = invoice_stats['service_amount']
            record.medicine_amount = invoice_stats['medicine_amount']
            record.insurance_amount = invoice_stats['insurance_amount']
            record.patient_amount = invoice_stats['patient_amount']

            # Get insurance statistics
            insurance_stats = self.get_insurance_statistics(record.date_from, record.date_to)
            record.insurance_percentage = insurance_stats['insurance_percentage']

            # Get purchase statistics
            purchase_stats = self.get_purchase_statistics(record.date_from, record.date_to)
            record.total_purchases = purchase_stats['total_purchases']
            record.purchase_amount = purchase_stats['total_amount']
            record.total_quantity = purchase_stats['total_quantity']

            # Count patients with/without insurance
            patient_with_ins, patient_without_ins = self._count_patients_by_insurance(
                record.date_from, record.date_to)
            record.patient_insurance_count = patient_with_ins
            record.patient_without_insurance_count = patient_without_ins

            # Get top services and products (serialize to text)
            top_services = self.get_service_statistics(record.date_from, record.date_to)
            record.top_services = str(top_services)  # Simple serialization

            top_products = self.get_product_statistics(record.date_from, record.date_to)
            record.top_products = str(top_products)  # Simple serialization

            # Generate revenue chart data
            # You'll need to implement this based on your charting requirements

        return True

    def _count_patients_by_insurance(self, start_date, end_date):
        """Count patients with and without insurance"""
        domain = [
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('state', '=', 'paid')
        ]

        invoices = self.env['clinic.invoice'].search(domain)

        # Get unique patients
        patients_with_insurance = set()
        patients_without_insurance = set()

        for invoice in invoices:
            patient_id = invoice.patient_id.id
            if invoice.insurance_amount > 0:
                patients_with_insurance.add(patient_id)
            else:
                patients_without_insurance.add(patient_id)

        return len(patients_with_insurance), len(patients_without_insurance)

    @api.model
    def get_invoice_statistics(self, start_date=None, end_date=None):
        """Lấy thống kê hóa đơn trong khoảng thời gian"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()

        domain = [
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('state', '=', 'paid')
        ]

        invoices = self.env['clinic.invoice'].search(domain)
        return {
            'total_invoices': len(invoices),
            'total_amount': sum(invoices.mapped('amount_total')),
            'service_amount': sum(invoices.mapped('service_amount')),
            'medicine_amount': sum(invoices.mapped('medicine_amount')),
            'insurance_amount': sum(invoices.mapped('insurance_amount')),
            'patient_amount': sum(invoices.mapped('patient_amount'))
        }

    @api.model
    def get_monthly_statistics(self, year=None):
        """Lấy thống kê theo tháng trong năm"""
        if not year:
            year = fields.Date.today().year

        result = []
        for month in range(1, 13):
            # Tính ngày đầu và cuối tháng
            start_date = fields.Date.to_string(datetime(year, month, 1))
            last_day = calendar.monthrange(year, month)[1]
            end_date = fields.Date.to_string(datetime(year, month, last_day))

            # Lấy hóa đơn trong tháng
            domain = [
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
                ('state', '=', 'paid')
            ]
            invoices = self.env['clinic.invoice'].search(domain)

            month_name = calendar.month_name[month]
            result.append({
                'month': month_name,
                'total_invoices': len(invoices),
                'total_amount': sum(invoices.mapped('amount_total')),
                'service_amount': sum(invoices.mapped('service_amount')),
                'medicine_amount': sum(invoices.mapped('medicine_amount'))
            })

        return result

    @api.model
    def get_service_statistics(self, start_date=None, end_date=None):
        """Lấy thống kê dịch vụ được sử dụng nhiều nhất"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()

        # Lấy tất cả các dòng dịch vụ từ hóa đơn đã thanh toán
        domain = [
            ('invoice_id.invoice_date', '>=', start_date),
            ('invoice_id.invoice_date', '<=', end_date),
            ('invoice_id.state', '=', 'paid'),
            ('service_id', '!=', False)
        ]

        service_lines = self.env['clinic.invoice.line'].search(domain)

        # Thống kê theo dịch vụ
        services_data = {}
        for line in service_lines:
            service_id = line.service_id.id
            if service_id not in services_data:
                services_data[service_id] = {
                    'name': line.service_id.name,
                    'count': 0,
                    'total_amount': 0
                }
            services_data[service_id]['count'] += line.quantity
            services_data[service_id]['total_amount'] += line.price_subtotal

        # Sắp xếp theo số lượng sử dụng
        result = sorted(services_data.values(), key=lambda x: x['count'], reverse=True)
        return result[:10]  # Top 10 dịch vụ

    @api.model
    def get_product_statistics(self, start_date=None, end_date=None):
        """Lấy thống kê thuốc được sử dụng nhiều nhất"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()

        # Lấy tất cả các dòng thuốc từ hóa đơn đã thanh toán
        domain = [
            ('invoice_id.invoice_date', '>=', start_date),
            ('invoice_id.invoice_date', '<=', end_date),
            ('invoice_id.state', '=', 'paid'),
            ('product_id', '!=', False)
        ]

        product_lines = self.env['clinic.invoice.line'].search(domain)

        # Thống kê theo thuốc
        products_data = {}
        for line in product_lines:
            product_id = line.product_id.id
            if product_id not in products_data:
                products_data[product_id] = {
                    'name': line.product_id.name,
                    'count': 0,
                    'total_amount': 0
                }
            products_data[product_id]['count'] += line.quantity
            products_data[product_id]['total_amount'] += line.price_subtotal

        # Sắp xếp theo số lượng sử dụng
        result = sorted(products_data.values(), key=lambda x: x['count'], reverse=True)
        return result[:10]  # Top 10 thuốc

    @api.model
    def get_insurance_statistics(self, start_date=None, end_date=None):
        """Lấy thống kê về bảo hiểm"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()

        domain = [
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('state', '=', 'paid')
        ]

        invoices = self.env['clinic.invoice'].search(domain)

        total_amount = sum(invoices.mapped('amount_total'))
        insurance_amount = sum(invoices.mapped('insurance_amount'))

        # Tính tỷ lệ bảo hiểm chi trả
        insurance_percentage = 0
        if total_amount > 0:
            insurance_percentage = (insurance_amount / total_amount) * 100

        return {
            'total_amount': total_amount,
            'insurance_amount': insurance_amount,
            'insurance_percentage': round(insurance_percentage, 2)
        }

    @api.model
    def get_purchase_statistics(self, start_date=None, end_date=None):
        """Lấy thống kê về nhập hàng"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()

        domain = [
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', '=', 'paid')
        ]

        purchases = self.env['clinic.purchase.order'].search(domain)

        return {
            'total_purchases': len(purchases),
            'total_amount': sum(purchases.mapped('amount_total')),
            'total_quantity': sum(purchase.line_ids.mapped('quantity') for purchase in purchases)
        }