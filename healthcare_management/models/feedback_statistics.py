# -*- coding: utf-8 -*-

from odoo import models, fields, tools


class FeedbackStatistics(models.Model):
    _name = 'healthcare.feedback.statistics'
    _description = 'Thống kê phản hồi của bệnh nhân'
    _auto = False
    _order = 'feedback_date desc'

    name = fields.Char(string='Mã phản hồi')
    patient_name = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True, tracking=True)
    department_name = fields.Many2one('clinic.department', string='Phòng ban', tracking=True)
    feedback_date = fields.Date(string='Ngày phản hồi')
    feedback_type = fields.Selection([
        ('compliment', 'Khen ngợi'),
        ('suggestion', 'Góp ý'),
        ('complaint', 'Khiếu nại'),
        ('question', 'Hỏi đáp'),
        ('other', 'Khác')
    ], string='Loại phản hồi')
    state = fields.Selection([
        ('new', 'Mới'),
        ('noted', 'Đã ghi nhận'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái')
    user_id = fields.Many2one('res.users', string='Người phụ trách')
    satisfaction_rating = fields.Selection([
        ('1', 'Rất không hài lòng'),
        ('2', 'Không hài lòng'),
        ('3', 'Bình thường'),
        ('4', 'Hài lòng'),
        ('5', 'Rất hài lòng')
    ], string='Đánh giá mức độ hài lòng')
    has_complaint = fields.Boolean(string='Có khiếu nại liên quan')

    month = fields.Char(string='Tháng', readonly=True)
    year = fields.Char(string='Năm', readonly=True)
    satisfaction_numeric = fields.Integer(string='Tổng đánh giá', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    fb.id as id,
                    fb.name as name,
                    fb.patient_name as patient_name,
                    fb.department_name as department_name,
                    fb.feedback_date as feedback_date,
                    fb.feedback_type as feedback_type,
                    fb.state as state,
                    fb.user_id as user_id,
                    fb.satisfaction_rating as satisfaction_rating,
                    CASE WHEN fb.complaint_id IS NOT NULL THEN true ELSE false END as has_complaint,
                    TO_CHAR(fb.feedback_date, 'MM') as month,
                    TO_CHAR(fb.feedback_date, 'YYYY') as year,
                    CASE 
                        WHEN fb.satisfaction_rating = '1' THEN 1
                        WHEN fb.satisfaction_rating = '2' THEN 2
                        WHEN fb.satisfaction_rating = '3' THEN 3
                        WHEN fb.satisfaction_rating = '4' THEN 4
                        WHEN fb.satisfaction_rating = '5' THEN 5
                        ELSE 0
                    END as satisfaction_numeric
                FROM
                    healthcare_patient_feedback fb
            )
        ''' % self._table)