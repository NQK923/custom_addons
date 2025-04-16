# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MedicalInspection(models.Model):
    _name = 'hospital.inspection'
    _description = 'Kiểm tra y tế'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string='Tên kiểm tra', required=True, tracking=True)
    certification_id = fields.Many2one('hospital.certification', string='Chứng nhận liên quan', tracking=True)

    date = fields.Date(string='Ngày kiểm tra', required=True, tracking=True)
    planned_date = fields.Date(string='Ngày dự kiến kiểm tra')

    inspector = fields.Char(string='Người/Đơn vị kiểm tra', tracking=True)
    result = fields.Selection([
        ('pending', 'Đang chờ'),
        ('passed', 'Đạt'),
        ('failed', 'Không đạt'),
        ('conditional', 'Đạt có điều kiện')
    ], string='Kết quả', default='pending', tracking=True)

    notes = fields.Text(string='Ghi chú')
    findings = fields.Text(string='Phát hiện')
    recommendations = fields.Text(string='Khuyến nghị')

    document = fields.Binary(string='Tài liệu kiểm tra', attachment=True)
    document_filename = fields.Char(string='Tên file tài liệu')

    corrective_action_required = fields.Boolean(string='Yêu cầu hành động khắc phục', default=False)
    corrective_action = fields.Text(string='Hành động khắc phục')
    corrective_deadline = fields.Date(string='Hạn khắc phục')
    corrective_completed = fields.Boolean(string='Đã hoàn thành khắc phục', default=False)

    staff_id = fields.Many2one('clinic.staff', string='Người phụ trách', tracking=True)
    state = fields.Selection([
        ('planned', 'Lên kế hoạch'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Đã hoàn thành'),
        ('canceled', 'Hủy bỏ')
    ], string='Trạng thái', default='planned', tracking=True)

    # Hành động chuyển trạng thái
    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'canceled'})

    def action_reset(self):
        self.write({'state': 'planned'})

    @api.onchange('result')
    def _onchange_result(self):
        if self.result == 'failed':
            self.corrective_action_required = True
        else:
            self.corrective_action_required = False
