# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PatientFeedback(models.Model):
    _name = 'healthcare.patient.feedback'
    _description = 'Phản hồi của bệnh nhân'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Mã phản hồi', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Bệnh nhân', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban', tracking=True)
    feedback_date = fields.Date(string='Ngày phản hồi', default=fields.Date.context_today, tracking=True)
    feedback_type = fields.Selection([
        ('compliment', 'Khen ngợi'),
        ('suggestion', 'Góp ý'),
        ('complaint', 'Khiếu nại'),
        ('question', 'Hỏi đáp'),
        ('other', 'Khác')
    ], string='Loại phản hồi', required=True, tracking=True)

    description = fields.Text(string='Nội dung phản hồi', required=True)
    state = fields.Selection([
        ('new', 'Mới'),
        ('noted', 'Đã ghi nhận'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='new', tracking=True)

    user_id = fields.Many2one('res.users', string='Người phụ trách', default=lambda self: self.env.user)

    satisfaction_rating = fields.Selection([
        ('1', 'Rất không hài lòng'),
        ('2', 'Không hài lòng'),
        ('3', 'Bình thường'),
        ('4', 'Hài lòng'),
        ('5', 'Rất hài lòng')
    ], string='Đánh giá mức độ hài lòng')

    complaint_id = fields.Many2one('healthcare.patient.complaint', string='Khiếu nại liên quan')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('healthcare.patient.feedback') or _('New')
        return super(PatientFeedback, self).create(vals_list)

    def action_note(self):
        self.write({'state': 'noted'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_new(self):
        self.write({'state': 'new'})

    def action_create_complaint(self):
        self.ensure_one()
        return {
            'name': _('Tạo khiếu nại mới'),
            'type': 'ir.actions.act_window',
            'res_model': 'healthcare.patient.complaint',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_feedback_id': self.id,
                'default_description': self.description,
            }
        }