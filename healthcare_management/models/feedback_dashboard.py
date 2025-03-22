# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from collections import defaultdict


class FeedbackDashboard(models.Model):
    _name = 'healthcare.feedback.dashboard'
    _description = 'Bảng điều khiển phản hồi bệnh nhân'
    _rec_name = 'name'

    name = fields.Char(string='Tên', default='Bảng điều khiển phản hồi')
    date_from = fields.Date(string='Từ ngày', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='Đến ngày', default=lambda self: fields.Date.today())

    # Thống kê tổng quan
    total_feedback = fields.Integer(string='Tổng số phản hồi', compute='_compute_statistics')
    total_compliments = fields.Integer(string='Số lượng khen ngợi', compute='_compute_statistics')
    total_complaints = fields.Integer(string='Số lượng khiếu nại', compute='_compute_statistics')
    total_suggestions = fields.Integer(string='Số lượng góp ý', compute='_compute_statistics')
    total_questions = fields.Integer(string='Số lượng hỏi đáp', compute='_compute_statistics')
    avg_satisfaction = fields.Float(string='Điểm hài lòng trung bình', compute='_compute_statistics', digits=(2, 1))

    # Thống kê theo phòng ban
    department_feedback_ids = fields.One2many('healthcare.feedback.dashboard.department', 'dashboard_id',
                                              string='Thống kê theo phòng ban',
                                              compute='_compute_department_statistics')

    # Dữ liệu cho biểu đồ (Lưu dạng JSON)
    feedback_by_type_data = fields.Text(string='Dữ liệu loại phản hồi', compute='_compute_chart_data')
    feedback_by_month_data = fields.Text(string='Dữ liệu theo tháng', compute='_compute_chart_data')
    satisfaction_distribution_data = fields.Text(string='Phân bố đánh giá', compute='_compute_chart_data')

    @api.depends('date_from', 'date_to')
    def _compute_statistics(self):
        for record in self:
            domain = [
                ('feedback_date', '>=', record.date_from),
                ('feedback_date', '<=', record.date_to)
            ]

            feedback_data = self.env['healthcare.feedback.statistics'].read_group(
                domain,
                fields=['feedback_type', 'satisfaction_numeric'],
                groupby=['feedback_type']
            )

            # Xác định khóa đếm trong kết quả read_group
            count_key = 'feedback_type_count'
            if feedback_data:
                # Tìm khóa đếm phù hợp trong kết quả
                possible_count_keys = ['__count', 'feedback_type_count']
                for key in possible_count_keys:
                    if key in feedback_data[0]:
                        count_key = key
                        break

            record.total_feedback = sum(item.get(count_key, 0) for item in feedback_data)
            record.total_compliments = sum(
                item.get(count_key, 0) for item in feedback_data if item['feedback_type'] == 'compliment')
            record.total_complaints = sum(
                item.get(count_key, 0) for item in feedback_data if item['feedback_type'] == 'complaint')
            record.total_suggestions = sum(
                item.get(count_key, 0) for item in feedback_data if item['feedback_type'] == 'suggestion')
            record.total_questions = sum(
                item.get(count_key, 0) for item in feedback_data if item['feedback_type'] == 'question')

            # Tính điểm hài lòng trung bình
            satisfaction_data = self.env['healthcare.feedback.statistics'].search(
                domain + [('satisfaction_numeric', '>', 0)]
            )

            if satisfaction_data:
                total_score = sum(data.satisfaction_numeric for data in satisfaction_data)
                record.avg_satisfaction = total_score / len(satisfaction_data)
            else:
                record.avg_satisfaction = 0.0

    @api.depends('date_from', 'date_to')
    def _compute_department_statistics(self):
        for record in self:
            record.department_feedback_ids = [(5, 0, 0)]  # Xóa các records hiện tại

            domain = [
                ('feedback_date', '>=', record.date_from),
                ('feedback_date', '<=', record.date_to),
                ('department_name', '!=', False)
            ]

            # Lấy thống kê theo phòng ban
            department_data = self.env['healthcare.feedback.statistics'].read_group(
                domain,
                fields=['department_name', 'satisfaction_numeric', 'feedback_type'],
                groupby=['department_name', 'feedback_type']
            )

            # Xác định khóa đếm trong kết quả read_group
            count_key = 'feedback_type_count'
            if department_data:
                # Tìm khóa đếm phù hợp trong kết quả
                possible_count_keys = ['__count', 'feedback_type_count']
                for key in possible_count_keys:
                    if key in department_data[0]:
                        count_key = key
                        break

            department_stats = defaultdict(lambda: {
                'department_name': False,
                'total': 0,
                'compliments': 0,
                'complaints': 0,
                'suggestions': 0,
                'questions': 0,
                'other': 0,
                'total_satisfaction': 0,
                'satisfaction_count': 0
            })

            for data in department_data:
                dept_id = data['department_name'][0] if data['department_name'] else False
                if not dept_id:
                    continue

                count = data.get(count_key, 0)
                feedback_type = data['feedback_type']
                department_stats[dept_id]['department_name'] = dept_id
                department_stats[dept_id]['total'] += count

                if feedback_type == 'compliment':
                    department_stats[dept_id]['compliments'] += count
                elif feedback_type == 'complaint':
                    department_stats[dept_id]['complaints'] += count
                elif feedback_type == 'suggestion':
                    department_stats[dept_id]['suggestions'] += count
                elif feedback_type == 'question':
                    department_stats[dept_id]['questions'] += count
                elif feedback_type == 'other':
                    department_stats[dept_id]['other'] += count

            # Tính điểm hài lòng trung bình cho mỗi phòng ban
            for dept_id in department_stats:
                satisfaction_data = self.env['healthcare.feedback.statistics'].search(
                    domain + [
                        ('department_name', '=', dept_id),
                        ('satisfaction_numeric', '>', 0)
                    ]
                )

                if satisfaction_data:
                    total_score = sum(data.satisfaction_numeric for data in satisfaction_data)
                    department_stats[dept_id]['total_satisfaction'] = total_score
                    department_stats[dept_id]['satisfaction_count'] = len(satisfaction_data)

            # Tạo records mới
            for dept_id, stats in department_stats.items():
                vals = {
                    'dashboard_id': record.id,
                    'department_name': stats['department_name'],
                    'total_feedback': stats['total'],
                    'compliments': stats['compliments'],
                    'complaints': stats['complaints'],
                    'suggestions': stats['suggestions'],
                    'questions': stats['questions'],
                    'others': stats['other'],
                }

                if stats['satisfaction_count'] > 0:
                    vals['avg_satisfaction'] = stats['total_satisfaction'] / stats['satisfaction_count']

                self.env['healthcare.feedback.dashboard.department'].create(vals)

    @api.depends('date_from', 'date_to')
    def _compute_chart_data(self):
        import json

        for record in self:
            domain = [
                ('feedback_date', '>=', record.date_from),
                ('feedback_date', '<=', record.date_to)
            ]

            # Dữ liệu cho biểu đồ loại phản hồi
            feedback_type_data = self.env['healthcare.feedback.statistics'].read_group(
                domain,
                fields=['feedback_type'],
                groupby=['feedback_type']
            )

            # Xác định khóa đếm trong kết quả read_group cho feedback_type_data
            count_key_type = 'feedback_type_count'
            if feedback_type_data:
                possible_count_keys = ['__count', 'feedback_type_count']
                for key in possible_count_keys:
                    if key in feedback_type_data[0]:
                        count_key_type = key
                        break

            feedback_type_chart = []
            for data in feedback_type_data:
                type_name = dict(self.env['healthcare.feedback.statistics']._fields['feedback_type'].selection).get(
                    data['feedback_type'], 'Khác')
                feedback_type_chart.append({
                    'type': type_name,
                    'count': data.get(count_key_type, 0)
                })

            record.feedback_by_type_data = json.dumps(feedback_type_chart)

            # Dữ liệu theo tháng
            feedback_month_data = self.env['healthcare.feedback.statistics'].read_group(
                domain,
                fields=['feedback_type'],
                groupby=['feedback_date:month', 'feedback_type'],
                orderby='feedback_date asc'
            )

            # Xác định khóa đếm trong kết quả read_group cho feedback_month_data
            count_key_month = 'feedback_type_count'
            if feedback_month_data:
                possible_count_keys = ['__count', 'feedback_type_count']
                for key in possible_count_keys:
                    if key in feedback_month_data[0]:
                        count_key_month = key
                        break

            month_data = defaultdict(lambda: {
                'month_name': '',
                'total': 0,
                'compliments': 0,
                'complaints': 0,
                'suggestions': 0,
                'questions': 0,
                'other': 0
            })

            month_names = {
                '01': 'Tháng 1', '02': 'Tháng 2', '03': 'Tháng 3', '04': 'Tháng 4',
                '05': 'Tháng 5', '06': 'Tháng 6', '07': 'Tháng 7', '08': 'Tháng 8',
                '09': 'Tháng 9', '10': 'Tháng 10', '11': 'Tháng 11', '12': 'Tháng 12'
            }

            for data in feedback_month_data:
                year = data.get('year')
                month = data.get('month')
                if year and month:
                    month_key = f"{year}-{month}"
                    month_data[month_key]['month_name'] = f"{month_names.get(month, month)}/{year}"
                    month_data[month_key]['total'] += data.get(count_key_month, 0)

                    feedback_type = data['feedback_type']
                    if feedback_type == 'compliment':
                        month_data[month_key]['compliments'] += data.get(count_key_month, 0)
                    elif feedback_type == 'complaint':
                        month_data[month_key]['complaints'] += data.get(count_key_month, 0)
                    elif feedback_type == 'suggestion':
                        month_data[month_key]['suggestions'] += data.get(count_key_month, 0)
                    elif feedback_type == 'question':
                        month_data[month_key]['questions'] += data.get(count_key_month, 0)
                    elif feedback_type == 'other':
                        month_data[month_key]['other'] += data.get(count_key_month, 0)

            # Sắp xếp theo tháng
            sorted_months = sorted(month_data.items(), key=lambda x: x[0])
            feedback_month_chart = [data for _, data in sorted_months]

            record.feedback_by_month_data = json.dumps(feedback_month_chart)

            # Dữ liệu phân bố đánh giá mức độ hài lòng
            satisfaction_data = self.env['healthcare.feedback.statistics'].read_group(
                domain + [('satisfaction_numeric', '>', 0)],
                fields=['satisfaction_rating'],
                groupby=['satisfaction_rating']
            )

            # Xác định khóa đếm trong kết quả read_group cho satisfaction_data
            count_key_satisfaction = 'satisfaction_rating_count'
            if satisfaction_data:
                possible_count_keys = ['__count', 'satisfaction_rating_count']
                for key in possible_count_keys:
                    if key in satisfaction_data[0]:
                        count_key_satisfaction = key
                        break

            satisfaction_chart = []
            satisfaction_labels = {
                '1': 'Rất không hài lòng',
                '2': 'Không hài lòng',
                '3': 'Bình thường',
                '4': 'Hài lòng',
                '5': 'Rất hài lòng'
            }

            for data in satisfaction_data:
                rating = data['satisfaction_rating']
                satisfaction_chart.append({
                    'rating': satisfaction_labels.get(rating, rating),
                    'count': data.get(count_key_satisfaction, 0)
                })

            record.satisfaction_distribution_data = json.dumps(satisfaction_chart)


class FeedbackDashboardDepartment(models.Model):
    _name = 'healthcare.feedback.dashboard.department'
    _description = 'Thống kê phản hồi theo phòng ban'

    dashboard_id = fields.Many2one('healthcare.feedback.dashboard', string='Bảng điều khiển')
    department_name = fields.Many2one('clinic.department', string='Phòng ban')
    total_feedback = fields.Integer(string='Tổng số phản hồi')
    compliments = fields.Integer(string='Khen ngợi')
    complaints = fields.Integer(string='Khiếu nại')
    suggestions = fields.Integer(string='Góp ý')
    questions = fields.Integer(string='Hỏi đáp')
    others = fields.Integer(string='Khác')
    avg_satisfaction = fields.Float(string='Điểm hài lòng TB', digits=(2, 1))