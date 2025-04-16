# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta

from odoo import models, fields, api


class ComplaintDashboard(models.Model):
    _name = 'healthcare.complaint.dashboard'
    _description = 'Bảng điều khiển khiếu nại bệnh nhân'
    _rec_name = 'name'

    name = fields.Char(string='Tên', default='Bảng điều khiển khiếu nại')
    date_from = fields.Date(string='Từ ngày', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='Đến ngày', default=lambda self: fields.Date.today())

    # Thống kê tổng quan
    total_complaints = fields.Integer(string='Tổng số khiếu nại', compute='_compute_statistics')
    new_complaints = fields.Integer(string='Khiếu nại mới', compute='_compute_statistics')
    in_progress_complaints = fields.Integer(string='Đang xử lý', compute='_compute_statistics')
    resolved_complaints = fields.Integer(string='Đã giải quyết', compute='_compute_statistics')
    cancelled_complaints = fields.Integer(string='Đã hủy', compute='_compute_statistics')
    avg_resolution_time = fields.Float(string='Thời gian giải quyết TB (ngày)', compute='_compute_statistics',
                                       digits=(10, 1))

    # Thống kê theo phân loại
    category_complaint_ids = fields.One2many('healthcare.complaint.dashboard.category', 'dashboard_id',
                                             string='Thống kê theo phân loại',
                                             compute='_compute_category_statistics')

    # Dữ liệu cho biểu đồ (Lưu dạng JSON)
    complaint_by_category_data = fields.Text(string='Dữ liệu theo phân loại', compute='_compute_chart_data')
    complaint_by_month_data = fields.Text(string='Dữ liệu theo tháng', compute='_compute_chart_data')

    @api.depends('date_from', 'date_to')
    def _compute_statistics(self):
        for record in self:
            domain = [
                ('complaint_date', '>=', record.date_from),
                ('complaint_date', '<=', record.date_to)
            ]

            complaint_data = self.env['healthcare.complaint.statistics'].read_group(
                domain,
                fields=['state', 'resolution_time'],
                groupby=['state']
            )

            # Xác định khóa đếm trong kết quả read_group
            count_key = 'state_count'
            if complaint_data:
                # Tìm khóa đếm phù hợp trong kết quả
                possible_count_keys = ['__count', 'state_count']
                for key in possible_count_keys:
                    if key in complaint_data[0]:
                        count_key = key
                        break

            record.total_complaints = sum(item.get(count_key, 0) for item in complaint_data)
            record.new_complaints = sum(
                item.get(count_key, 0) for item in complaint_data if item.get('state') == 'new')
            record.in_progress_complaints = sum(
                item.get(count_key, 0) for item in complaint_data if item.get('state') == 'in_progress')
            record.resolved_complaints = sum(
                item.get(count_key, 0) for item in complaint_data if item.get('state') == 'resolved')
            record.cancelled_complaints = sum(
                item.get(count_key, 0) for item in complaint_data if item.get('state') == 'cancelled')

            # Tính thời gian giải quyết trung bình
            resolution_data = self.env['healthcare.complaint.statistics'].search(
                domain + [('resolution_time', '>', 0)]
            )

            if resolution_data:
                total_days = sum(data.resolution_time for data in resolution_data)
                record.avg_resolution_time = total_days / len(resolution_data)
            else:
                record.avg_resolution_time = 0.0

    @api.depends('date_from', 'date_to')
    def _compute_category_statistics(self):
        for record in self:
            # Clear previous records
            record.category_complaint_ids = [(5, 0, 0)]

            # Define the date range for our queries
            date_from_str = record.date_from
            date_to_str = record.date_to

            # Use direct SQL to ensure accurate counts
            self.env.cr.execute("""
                SELECT 
                    category,
                    COUNT(id) AS total_complaints,
                    SUM(CASE WHEN state = 'new' THEN 1 ELSE 0 END) AS new_count,
                    SUM(CASE WHEN state = 'in_progress' THEN 1 ELSE 0 END) AS in_progress_count,
                    SUM(CASE WHEN state = 'resolved' THEN 1 ELSE 0 END) AS resolved_count,
                    SUM(CASE WHEN state = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_count,
                    AVG(CASE WHEN resolution_time > 0 THEN resolution_time ELSE NULL END) AS avg_resolution_time
                FROM 
                    healthcare_complaint_statistics
                WHERE 
                    complaint_date >= %s AND complaint_date <= %s
                GROUP BY 
                    category
                ORDER BY 
                    category
            """, (date_from_str, date_to_str))

            # Get the results
            category_stats = self.env.cr.dictfetchall()

            # Create category complaint records
            category_complaint_commands = []

            # Mapping for category values to display names
            category_mapping = dict(self.env['healthcare.patient.complaint']._fields['category'].selection)

            for stats in category_stats:
                # Convert None to 0 for integer fields
                for field in ['new_count', 'in_progress_count', 'resolved_count', 'cancelled_count',
                              'total_complaints']:
                    if stats.get(field) is None:
                        stats[field] = 0

                # Default avg values to 0 if None
                if stats.get('avg_resolution_time') is None:
                    stats['avg_resolution_time'] = 0

                # Get category display name
                category_value = stats.get('category')
                category_name = category_mapping.get(category_value, 'Không xác định')

                category_complaint_commands.append((0, 0, {
                    'dashboard_id': record.id,
                    'category': category_value,
                    'category_name': category_name,
                    'total_complaints': stats['total_complaints'],
                    'new_count': stats['new_count'],
                    'in_progress_count': stats['in_progress_count'],
                    'resolved_count': stats['resolved_count'],
                    'cancelled_count': stats['cancelled_count'],
                    'avg_resolution_time': stats['avg_resolution_time'],
                }))

            # Update the one2many field with the new records
            if category_complaint_commands:
                record.category_complaint_ids = category_complaint_commands

    @api.depends('date_from', 'date_to')
    def _compute_chart_data(self):
        import json

        for record in self:
            domain = [
                ('complaint_date', '>=', record.date_from),
                ('complaint_date', '<=', record.date_to)
            ]

            # Dữ liệu cho biểu đồ phân loại khiếu nại
            category_data = self.env['healthcare.complaint.statistics'].read_group(
                domain,
                fields=['category'],
                groupby=['category']
            )

            # Xác định khóa đếm trong kết quả read_group cho category_data
            count_key_category = 'category_count'
            if category_data:
                possible_count_keys = ['__count', 'category_count']
                for key in possible_count_keys:
                    if key in category_data[0]:
                        count_key_category = key
                        break

            category_chart = []
            for data in category_data:
                # Safely get category
                category_value = data.get('category', 'other')
                category_name = dict(self.env['healthcare.patient.complaint']._fields['category'].selection).get(
                    category_value, 'Khác')
                category_chart.append({
                    'category': category_name,
                    'count': data.get(count_key_category, 0)
                })

            record.complaint_by_category_data = json.dumps(category_chart)

            # Dữ liệu theo tháng
            complaint_month_data = self.env['healthcare.complaint.statistics'].read_group(
                domain,
                fields=['state'],
                groupby=['complaint_date:month', 'state'],
                orderby='complaint_date asc'
            )

            # Xác định khóa đếm trong kết quả read_group cho complaint_month_data
            count_key_month = 'state_count'
            if complaint_month_data:
                possible_count_keys = ['__count', 'state_count']
                for key in possible_count_keys:
                    if key in complaint_month_data[0]:
                        count_key_month = key
                        break

            month_data = defaultdict(lambda: {
                'month_name': '',
                'total': 0,
                'new': 0,
                'in_progress': 0,
                'resolved': 0,
                'cancelled': 0
            })

            month_names = {
                '01': 'Tháng 1', '02': 'Tháng 2', '03': 'Tháng 3', '04': 'Tháng 4',
                '05': 'Tháng 5', '06': 'Tháng 6', '07': 'Tháng 7', '08': 'Tháng 8',
                '09': 'Tháng 9', '10': 'Tháng 10', '11': 'Tháng 11', '12': 'Tháng 12'
            }

            for data in complaint_month_data:
                year = data.get('year')
                month = data.get('month')
                if year and month:
                    month_key = f"{year}-{month}"
                    month_data[month_key]['month_name'] = f"{month_names.get(month, month)}/{year}"
                    month_data[month_key]['total'] += data.get(count_key_month, 0)

                    # Safely get state
                    state = data.get('state', 'other')
                    if state == 'new':
                        month_data[month_key]['new'] += data.get(count_key_month, 0)
                    elif state == 'in_progress':
                        month_data[month_key]['in_progress'] += data.get(count_key_month, 0)
                    elif state == 'resolved':
                        month_data[month_key]['resolved'] += data.get(count_key_month, 0)
                    elif state == 'cancelled':
                        month_data[month_key]['cancelled'] += data.get(count_key_month, 0)

            # Sắp xếp theo tháng
            sorted_months = sorted(month_data.items(), key=lambda x: x[0])
            complaint_month_chart = [data for _, data in sorted_months]

            record.complaint_by_month_data = json.dumps(complaint_month_chart)


class ComplaintDashboardCategory(models.TransientModel):
    _name = 'healthcare.complaint.dashboard.category'
    _description = 'Thống kê khiếu nại theo phân loại'

    dashboard_id = fields.Many2one('healthcare.complaint.dashboard', string='Bảng điều khiển')
    category = fields.Char(string='Phân loại')
    category_name = fields.Char(string='Tên phân loại')
    total_complaints = fields.Integer(string='Tổng số khiếu nại')
    new_count = fields.Integer(string='Mới')
    in_progress_count = fields.Integer(string='Đang xử lý')
    resolved_count = fields.Integer(string='Đã giải quyết')
    cancelled_count = fields.Integer(string='Đã hủy')
    avg_resolution_time = fields.Float(string='Thời gian xử lý TB', digits=(10, 1))
