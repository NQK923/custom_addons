# -*- coding: utf-8 -*-

from odoo import models, fields, tools


class ComplaintStatistics(models.Model):
    _name = 'healthcare.complaint.statistics'
    _description = 'Thống kê khiếu nại của bệnh nhân'
    _auto = False
    _order = 'complaint_date desc'

    name = fields.Char(string='Mã khiếu nại')
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True, tracking=True)
    complaint_date = fields.Date(string='Ngày khiếu nại')
    category = fields.Selection([
        ('service', 'Dịch vụ'),
        ('staff', 'Nhân viên'),
        ('facility', 'Cơ sở vật chất'),
        ('billing', 'Thanh toán'),
        ('other', 'Khác')
    ], string='Phân loại khiếu nại')
    priority = fields.Selection([
        ('0', 'Thấp'),
        ('1', 'Trung bình'),
        ('2', 'Cao')
    ], string='Mức độ ưu tiên')
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_progress', 'Đang xử lý'),
        ('resolved', 'Đã giải quyết'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái')
    user_id = fields.Many2one('res.users', string='Người phụ trách')
    feedback_id = fields.Many2one('healthcare.patient.feedback', string='Phản hồi liên quan')
    resolution_time = fields.Integer(string='Thời gian giải quyết (ngày)', readonly=True)

    month = fields.Char(string='Tháng', readonly=True)
    year = fields.Char(string='Năm', readonly=True)
    satisfaction_rating = fields.Selection([
        ('1', 'Rất không hài lòng'),
        ('2', 'Không hài lòng'),
        ('3', 'Bình thường'),
        ('4', 'Hài lòng'),
        ('5', 'Rất hài lòng')
    ], string='Đánh giá sau giải quyết')
    satisfaction_numeric = fields.Integer(string='Điểm đánh giá', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    cp.id as id,
                    cp.name as name,
                    cp.patient_id as patient_id,
                    cp.complaint_date as complaint_date,
                    cp.category as category,
                    cp.priority as priority,
                    cp.state as state,
                    cp.user_id as user_id,
                    cp.feedback_id as feedback_id,
                    CASE 
                        WHEN cp.resolved_date IS NOT NULL AND cp.complaint_date IS NOT NULL
                        THEN (cp.resolved_date - cp.complaint_date)::integer
                        ELSE NULL
                    END as resolution_time,
                    TO_CHAR(cp.complaint_date, 'MM') as month,
                    TO_CHAR(cp.complaint_date, 'YYYY') as year,
                    cp.satisfaction_rating as satisfaction_rating,
                    CASE 
                        WHEN cp.satisfaction_rating = '1' THEN 1
                        WHEN cp.satisfaction_rating = '2' THEN 2
                        WHEN cp.satisfaction_rating = '3' THEN 3
                        WHEN cp.satisfaction_rating = '4' THEN 4
                        WHEN cp.satisfaction_rating = '5' THEN 5
                        ELSE 0
                    END as satisfaction_numeric
                FROM
                    healthcare_patient_complaint cp
            )
        ''' % self._table)