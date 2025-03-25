# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from collections import defaultdict
import json


class InvoiceDashboard(models.Model):
    _name = 'invoice.dashboard'
    _description = 'Bảng điều khiển phân tích hóa đơn'
    _rec_name = 'name'

    name = fields.Char(string='Tên', default='Bảng điều khiển hóa đơn')
    date_from = fields.Date(string='Từ ngày', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='Đến ngày', default=lambda self: fields.Date.today())

    # Thống kê tổng quan
    total_invoices = fields.Integer(string='Tổng số hóa đơn', compute='_compute_statistics')
    total_paid_invoices = fields.Integer(string='Số hóa đơn đã thanh toán', compute='_compute_statistics')
    total_confirmed_invoices = fields.Integer(string='Số hóa đơn đã xác nhận', compute='_compute_statistics')
    total_cancelled_invoices = fields.Integer(string='Số hóa đơn đã hủy', compute='_compute_statistics')

    # Thống kê tài chính
    total_revenue = fields.Float(string='Tổng doanh thu', compute='_compute_statistics')
    total_service_revenue = fields.Float(string='Doanh thu dịch vụ', compute='_compute_statistics')
    total_medicine_revenue = fields.Float(string='Doanh thu thuốc', compute='_compute_statistics')
    total_insurance_amount = fields.Float(string='Tổng bảo hiểm chi trả', compute='_compute_statistics')
    total_patient_amount = fields.Float(string='Tổng bệnh nhân chi trả', compute='_compute_statistics')

    # Số lượng dịch vụ và thuốc
    total_services = fields.Integer(string='Tổng số dịch vụ', compute='_compute_statistics')
    total_products = fields.Integer(string='Tổng số thuốc', compute='_compute_statistics')

    # Dữ liệu cho biểu đồ (Lưu dạng JSON)
    revenue_by_day_data = fields.Text(string='Doanh thu theo ngày', compute='_compute_chart_data')
    revenue_by_month_data = fields.Text(string='Doanh thu theo tháng', compute='_compute_chart_data')
    service_vs_medicine_data = fields.Text(string='Dịch vụ vs Thuốc', compute='_compute_chart_data')
    invoice_status_data = fields.Text(string='Trạng thái hóa đơn', compute='_compute_chart_data')
    insurance_vs_patient_data = fields.Text(string='Bảo hiểm vs Bệnh nhân', compute='_compute_chart_data')

    # Dữ liệu phân tích chi tiết
    top_services_data = fields.Text(string='Top dịch vụ', compute='_compute_top_data')
    top_products_data = fields.Text(string='Top thuốc', compute='_compute_top_data')
    top_patients_data = fields.Text(string='Top bệnh nhân', compute='_compute_top_data')
    monthly_comparison_data = fields.Text(string='So sánh theo tháng', compute='_compute_comparison_data')

    @api.depends('date_from', 'date_to')
    def _compute_statistics(self):
        for record in self:
            domain = [
                ('invoice_date', '>=', record.date_from),
                ('invoice_date', '<=', record.date_to)
            ]

            # Lấy tổng số hóa đơn theo trạng thái
            invoice_data = self.env['invoice.statistics'].read_group(
                domain,
                fields=['state', 'amount_total', 'service_amount', 'medicine_amount',
                        'insurance_amount', 'patient_amount', 'service_count', 'product_count'],
                groupby=['state']
            )

            # Xác định khóa đếm trong kết quả read_group
            count_key = 'state_count'
            if invoice_data:
                # Tìm khóa đếm phù hợp trong kết quả
                possible_count_keys = ['__count', 'state_count']
                for key in possible_count_keys:
                    if key in invoice_data[0]:
                        count_key = key
                        break

            # Tính tổng số hóa đơn
            record.total_invoices = sum(item.get(count_key, 0) for item in invoice_data)
            record.total_paid_invoices = sum(
                item.get(count_key, 0) for item in invoice_data if item.get('state') == 'paid')
            record.total_confirmed_invoices = sum(
                item.get(count_key, 0) for item in invoice_data if item.get('state') == 'confirmed')
            record.total_cancelled_invoices = sum(
                item.get(count_key, 0) for item in invoice_data if item.get('state') == 'cancelled')

            # Tính tổng doanh thu từ hóa đơn đã thanh toán
            revenue_data = self.env['invoice.statistics'].read_group(
                domain + [('state', '=', 'paid')],
                fields=['amount_total', 'service_amount', 'medicine_amount',
                        'insurance_amount', 'patient_amount', 'service_count', 'product_count'],
                groupby=[]
            )

            if revenue_data:
                record.total_revenue = revenue_data[0].get('amount_total', 0)
                record.total_service_revenue = revenue_data[0].get('service_amount', 0)
                record.total_medicine_revenue = revenue_data[0].get('medicine_amount', 0)
                record.total_insurance_amount = revenue_data[0].get('insurance_amount', 0)
                record.total_patient_amount = revenue_data[0].get('patient_amount', 0)

                # Tính tổng số dịch vụ và thuốc
                record.total_services = revenue_data[0].get('service_count', 0)
                record.total_products = revenue_data[0].get('product_count', 0)
            else:
                record.total_revenue = 0
                record.total_service_revenue = 0
                record.total_medicine_revenue = 0
                record.total_insurance_amount = 0
                record.total_patient_amount = 0
                record.total_services = 0
                record.total_products = 0

    @api.depends('date_from', 'date_to')
    def _compute_chart_data(self):
        for record in self:
            domain = [
                ('invoice_date', '>=', record.date_from),
                ('invoice_date', '<=', record.date_to),
                ('state', '=', 'paid')
            ]

            # 1. Doanh thu theo ngày
            day_data = self.env['invoice.statistics'].read_group(
                domain,
                fields=['amount_total', 'service_amount', 'medicine_amount', 'day', 'month', 'year'],
                groupby=['day', 'month', 'year']
            )

            # Xác định khóa đếm
            count_key_day = '__count'
            if day_data and len(day_data) > 0:
                for key in ['__count', 'day_count']:
                    if key in day_data[0]:
                        count_key_day = key
                        break

            # Chuyển đổi kết quả thành dữ liệu biểu đồ và sắp xếp theo ngày
            revenue_by_day = []
            for item in day_data:
                day_val = item.get('day')
                month_val = item.get('month')
                year_val = item.get('year')
                if day_val and month_val and year_val:
                    date_label = f"{day_val}/{month_val}/{year_val}"
                    revenue_by_day.append({
                        'day': date_label,
                        'date_sort': f"{year_val}-{month_val}-{day_val}",  # Format for sorting
                        'total': item.get('amount_total', 0),
                        'service': item.get('service_amount', 0),
                        'medicine': item.get('medicine_amount', 0),
                        'count': item.get(count_key_day, 0)
                    })

            # Sort by date
            revenue_by_day.sort(key=lambda x: x['date_sort'])

            # Remove the sorting field before JSON conversion
            for item in revenue_by_day:
                if 'date_sort' in item:
                    del item['date_sort']

            record.revenue_by_day_data = json.dumps(revenue_by_day)

            # 2. Doanh thu theo tháng
            month_data = self.env['invoice.statistics'].read_group(
                domain,
                fields=['amount_total', 'service_amount', 'medicine_amount', 'month', 'year'],
                groupby=['month', 'year']
            )

            # Định nghĩa tên tháng
            month_names = {
                '01': 'Tháng 1', '02': 'Tháng 2', '03': 'Tháng 3', '04': 'Tháng 4',
                '05': 'Tháng 5', '06': 'Tháng 6', '07': 'Tháng 7', '08': 'Tháng 8',
                '09': 'Tháng 9', '10': 'Tháng 10', '11': 'Tháng 11', '12': 'Tháng 12'
            }

            # Xác định khóa đếm cho tháng
            count_key_month = '__count'
            if month_data and len(month_data) > 0:
                for key in ['__count', 'month_count']:
                    if key in month_data[0]:
                        count_key_month = key
                        break

            revenue_by_month = []
            for item in month_data:
                month = item.get('month')
                year = item.get('year')
                if month and year:
                    month_name = month_names.get(month, month)
                    revenue_by_month.append({
                        'month': f"{month_name}/{year}",
                        'month_sort': f"{year}-{month}",  # For sorting
                        'total': item.get('amount_total', 0),
                        'service': item.get('service_amount', 0),
                        'medicine': item.get('medicine_amount', 0),
                        'count': item.get(count_key_month, 0)
                    })

            # Sort by year and month
            revenue_by_month.sort(key=lambda x: x['month_sort'])

            # Remove the sorting field before JSON conversion
            for item in revenue_by_month:
                if 'month_sort' in item:
                    del item['month_sort']

            record.revenue_by_month_data = json.dumps(revenue_by_month)

            # 3. Dịch vụ vs Thuốc (tổng thể)
            service_vs_medicine = {
                'labels': ['Dịch vụ', 'Thuốc'],
                'data': [record.total_service_revenue, record.total_medicine_revenue]
            }

            record.service_vs_medicine_data = json.dumps(service_vs_medicine)

            # 4. Bảo hiểm vs Bệnh nhân chi trả
            insurance_vs_patient = {
                'labels': ['Bảo hiểm chi trả', 'Bệnh nhân chi trả'],
                'data': [record.total_insurance_amount, record.total_patient_amount]
            }

            record.insurance_vs_patient_data = json.dumps(insurance_vs_patient)

            # 5. Trạng thái hóa đơn
            status_data = self.env['invoice.statistics'].read_group(
                [
                    ('invoice_date', '>=', record.date_from),
                    ('invoice_date', '<=', record.date_to)
                ],
                fields=['state'],
                groupby=['state']
            )

            # Xác định khóa đếm
            count_key_status = '__count'
            if status_data and len(status_data) > 0:
                for key in ['__count', 'state_count']:
                    if key in status_data[0]:
                        count_key_status = key
                        break

            status_labels = {
                'draft': 'Nháp',
                'confirmed': 'Đã xác nhận',
                'paid': 'Đã thanh toán',
                'cancelled': 'Đã hủy'
            }

            invoice_status = []
            for item in status_data:
                state = item.get('state')
                if state:
                    invoice_status.append({
                        'status': status_labels.get(state, state),
                        'count': item.get(count_key_status, 0)
                    })

            record.invoice_status_data = json.dumps(invoice_status)

    @api.depends('date_from', 'date_to')
    def _compute_top_data(self):
        """Tính toán dữ liệu cho Top dịch vụ, thuốc và bệnh nhân"""
        for record in self:
            domain = [
                ('invoice_date', '>=', record.date_from),
                ('invoice_date', '<=', record.date_to),
                ('state', '=', 'paid')
            ]

            # 1. Top dịch vụ
            self.env.cr.execute("""
                SELECT 
                    s.service_name as name,
                    COUNT(l.id) as count,
                    SUM(l.price_subtotal) as total
                FROM 
                    clinic_invoice_line l
                JOIN 
                    clinic_service s ON l.service_id = s.id
                JOIN 
                    clinic_invoice i ON l.invoice_id = i.id
                WHERE 
                    i.invoice_date >= %s AND 
                    i.invoice_date <= %s AND 
                    i.state = 'paid' AND
                    l.service_id IS NOT NULL
                GROUP BY 
                    s.service_name
                ORDER BY 
                    total DESC
                LIMIT 10
            """, (record.date_from, record.date_to))

            top_services = []
            for row in self.env.cr.dictfetchall():
                top_services.append({
                    'name': row['name'],
                    'count': row['count'],
                    'total': row['total']
                })

            record.top_services_data = json.dumps(top_services)

            # 2. Top thuốc
            self.env.cr.execute("""
                SELECT 
                    p.name as name,
                    COUNT(l.id) as count,
                    SUM(l.price_subtotal) as total
                FROM 
                    clinic_invoice_line l
                JOIN 
                    pharmacy_product p ON l.product_id = p.id
                JOIN 
                    clinic_invoice i ON l.invoice_id = i.id
                WHERE 
                    i.invoice_date >= %s AND 
                    i.invoice_date <= %s AND 
                    i.state = 'paid' AND
                    l.product_id IS NOT NULL
                GROUP BY 
                    p.name
                ORDER BY 
                    total DESC
                LIMIT 10
            """, (record.date_from, record.date_to))

            top_products = []
            for row in self.env.cr.dictfetchall():
                top_products.append({
                    'name': row['name'],
                    'count': row['count'],
                    'total': row['total']
                })

            record.top_products_data = json.dumps(top_products)

            # 3. Top bệnh nhân
            self.env.cr.execute("""
                SELECT 
                    p.name as name,
                    COUNT(i.id) as count,
                    SUM(i.amount_total) as total
                FROM 
                    clinic_invoice i
                JOIN 
                    clinic_patient p ON i.patient_id = p.id
                WHERE 
                    i.invoice_date >= %s AND 
                    i.invoice_date <= %s AND 
                    i.state = 'paid'
                GROUP BY 
                    p.name
                ORDER BY 
                    total DESC
                LIMIT 10
            """, (record.date_from, record.date_to))

            top_patients = []
            for row in self.env.cr.dictfetchall():
                top_patients.append({
                    'name': row['name'],
                    'count': row['count'],
                    'total': row['total']
                })

            record.top_patients_data = json.dumps(top_patients)

    @api.depends('date_from', 'date_to')
    def _compute_comparison_data(self):
        """So sánh doanh thu tháng hiện tại với tháng trước"""
        for record in self:
            # Tính số ngày trong khoảng thời gian đã chọn
            delta = record.date_to - record.date_from
            days = delta.days

            # Tính thời gian của kỳ trước đó
            previous_date_to = record.date_from - timedelta(days=1)
            previous_date_from = previous_date_to - timedelta(days=days)

            # Lấy dữ liệu doanh thu của kỳ hiện tại
            current_data = self.env['invoice.statistics'].read_group(
                [
                    ('invoice_date', '>=', record.date_from),
                    ('invoice_date', '<=', record.date_to),
                    ('state', '=', 'paid')
                ],
                fields=['amount_total', 'service_amount', 'medicine_amount'],
                groupby=[]
            )

            # Lấy dữ liệu doanh thu của kỳ trước
            previous_data = self.env['invoice.statistics'].read_group(
                [
                    ('invoice_date', '>=', previous_date_from),
                    ('invoice_date', '<=', previous_date_to),
                    ('state', '=', 'paid')
                ],
                fields=['amount_total', 'service_amount', 'medicine_amount'],
                groupby=[]
            )

            # Tính tỷ lệ tăng trưởng
            current_total = current_data[0]['amount_total'] if current_data else 0
            previous_total = previous_data[0]['amount_total'] if previous_data else 0

            current_service = current_data[0]['service_amount'] if current_data else 0
            previous_service = previous_data[0]['service_amount'] if previous_data else 0

            current_medicine = current_data[0]['medicine_amount'] if current_data else 0
            previous_medicine = previous_data[0]['medicine_amount'] if previous_data else 0

            # Tính tỷ lệ % tăng trưởng
            def calculate_growth(current, previous):
                if previous == 0:
                    return 100.0 if current > 0 else 0.0
                return ((current - previous) / previous) * 100

            comparison_data = {
                'current_period': f"{record.date_from} - {record.date_to}",
                'previous_period': f"{previous_date_from} - {previous_date_to}",
                'total': {
                    'current': current_total,
                    'previous': previous_total,
                    'growth': calculate_growth(current_total, previous_total)
                },
                'service': {
                    'current': current_service,
                    'previous': previous_service,
                    'growth': calculate_growth(current_service, previous_service)
                },
                'medicine': {
                    'current': current_medicine,
                    'previous': previous_medicine,
                    'growth': calculate_growth(current_medicine, previous_medicine)
                }
            }

            record.monthly_comparison_data = json.dumps(comparison_data)