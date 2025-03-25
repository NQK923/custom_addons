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
                item.get(count_key, 0) for item in feedback_data if item.get('feedback_type') == 'compliment')
            record.total_complaints = sum(
                item.get(count_key, 0) for item in feedback_data if item.get('feedback_type') == 'complaint')
            record.total_suggestions = sum(
                item.get(count_key, 0) for item in feedback_data if item.get('feedback_type') == 'suggestion')
            record.total_questions = sum(
                item.get(count_key, 0) for item in feedback_data if item.get('feedback_type') == 'question')

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
            # Clear previous records
            record.department_feedback_ids = [(5, 0, 0)]

            # Define the date range for our queries
            date_from_str = record.date_from
            date_to_str = record.date_to

            # Use direct SQL to ensure accurate counts
            # This query gets all department stats in one go
            self.env.cr.execute("""
                SELECT 
                    d.id AS department_id,
                    d.name AS department_name,
                    COUNT(fs.id) AS total_feedback,
                    SUM(CASE WHEN fs.feedback_type = 'compliment' THEN 1 ELSE 0 END) AS compliments,
                    SUM(CASE WHEN fs.feedback_type = 'complaint' THEN 1 ELSE 0 END) AS complaints,
                    SUM(CASE WHEN fs.feedback_type = 'suggestion' THEN 1 ELSE 0 END) AS suggestions,
                    SUM(CASE WHEN fs.feedback_type = 'question' THEN 1 ELSE 0 END) AS questions,
                    SUM(CASE WHEN fs.feedback_type NOT IN ('compliment', 'complaint', 'suggestion', 'question') 
                            OR fs.feedback_type IS NULL THEN 1 ELSE 0 END) AS others,
                    AVG(CASE WHEN fs.satisfaction_numeric > 0 THEN fs.satisfaction_numeric ELSE NULL END) AS avg_satisfaction
                FROM 
                    healthcare_feedback_statistics fs
                JOIN 
                    clinic_department d ON fs.department_id = d.id
                WHERE 
                    fs.feedback_date >= %s AND fs.feedback_date <= %s
                GROUP BY 
                    d.id, d.name
                ORDER BY 
                    d.name
            """, (date_from_str, date_to_str))

            # Get the results
            department_stats = self.env.cr.dictfetchall()

            # Create department feedback records
            department_feedback_commands = []
            for stats in department_stats:
                # Convert None to 0 for integer fields
                for field in ['compliments', 'complaints', 'suggestions', 'questions', 'others', 'total_feedback']:
                    if stats.get(field) is None:
                        stats[field] = 0

                # Default avg_satisfaction to 0 if None
                if stats.get('avg_satisfaction') is None:
                    stats['avg_satisfaction'] = 0

                department_feedback_commands.append((0, 0, {
                    'dashboard_id': record.id,
                    'department_id': stats['department_id'],
                    'department_name': stats['department_name'],
                    'total_feedback': stats['total_feedback'],
                    'compliments': stats['compliments'],
                    'complaints': stats['complaints'],
                    'suggestions': stats['suggestions'],
                    'questions': stats['questions'],
                    'others': stats['others'],
                    'avg_satisfaction': stats['avg_satisfaction'],
                }))

            # Update the one2many field with the new records
            if department_feedback_commands:
                record.department_feedback_ids = department_feedback_commands

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
                # Safely get feedback_type
                feedback_type = data.get('feedback_type', 'other')
                type_name = dict(self.env['healthcare.feedback.statistics']._fields['feedback_type'].selection).get(
                    feedback_type, 'Khác')
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

                    # Safely get feedback_type
                    feedback_type = data.get('feedback_type', 'other')
                    if feedback_type == 'compliment':
                        month_data[month_key]['compliments'] += data.get(count_key_month, 0)
                    elif feedback_type == 'complaint':
                        month_data[month_key]['complaints'] += data.get(count_key_month, 0)
                    elif feedback_type == 'suggestion':
                        month_data[month_key]['suggestions'] += data.get(count_key_month, 0)
                    elif feedback_type == 'question':
                        month_data[month_key]['questions'] += data.get(count_key_month, 0)
                    else:
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
                # Safely get satisfaction_rating
                rating = data.get('satisfaction_rating', '')
                satisfaction_chart.append({
                    'rating': satisfaction_labels.get(rating, rating),
                    'count': data.get(count_key_satisfaction, 0)
                })

            record.satisfaction_distribution_data = json.dumps(satisfaction_chart)


class FeedbackDashboardDepartment(models.TransientModel):
    _name = 'healthcare.feedback.dashboard.department'
    _description = 'Thống kê phản hồi theo phòng ban'

    dashboard_id = fields.Many2one('healthcare.feedback.dashboard', string='Bảng điều khiển')
    department_id = fields.Many2one('clinic.department', string='Phòng ban')
    department_name = fields.Char(string='Tên phòng ban')
    total_feedback = fields.Integer(string='Tổng số phản hồi')
    compliments = fields.Integer(string='Khen ngợi')
    complaints = fields.Integer(string='Khiếu nại')
    suggestions = fields.Integer(string='Góp ý')
    questions = fields.Integer(string='Hỏi đáp')
    others = fields.Integer(string='Khác')
    avg_satisfaction = fields.Float(string='Điểm hài lòng TB', digits=(2, 1))