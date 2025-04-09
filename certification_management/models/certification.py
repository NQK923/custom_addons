# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MedicalCertification(models.Model):
    _name = 'hospital.certification'
    _description = 'Chứng nhận y tế'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date'

    name = fields.Char(string='Tên chứng nhận', required=True, tracking=True)
    number = fields.Char(string='Số hiệu', required=True, tracking=True)
    certification_type = fields.Selection([
        ('operation', 'Giấy phép hoạt động'),
        ('quality', 'Chứng nhận chất lượng'),
        ('safety', 'Chứng nhận an toàn'),
        ('environment', 'Chứng nhận môi trường'),
        ('other', 'Khác')
    ], string='Loại chứng nhận', required=True, tracking=True)

    issue_date = fields.Date(string='Ngày cấp', required=True, tracking=True)
    expiry_date = fields.Date(string='Ngày hết hạn', required=True, tracking=True)
    authority = fields.Char(string='Cơ quan cấp', required=True, tracking=True)
    description = fields.Text(string='Mô tả')

    document = fields.Binary(string='Tài liệu', attachment=True)
    document_filename = fields.Char(string='Tên file tài liệu')

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('valid', 'Có hiệu lực'),
        ('expiring', 'Sắp hết hạn'),
        ('expired', 'Hết hạn'),
        ('renewed', 'Đã gia hạn')
    ], string='Trạng thái', default='draft', tracking=True)

    staff_id = fields.Many2one('clinic.staff', string='Người phụ trách', tracking=True)
    department_id = fields.Many2one('clinic.department', string='Phòng ban liên quan')

    renewal_date = fields.Date(string='Ngày gia hạn tiếp theo')
    renewal_reminder = fields.Boolean(string='Nhắc nhở gia hạn', default=True)
    reminder_days = fields.Integer(string='Số ngày nhắc trước khi hết hạn', default=30)

    inspection_ids = fields.One2many('hospital.inspection', 'certification_id',
                                     string='Lịch sử kiểm tra')
    active = fields.Boolean(default=True)

    # Tính số ngày còn lại
    days_remaining = fields.Integer(string='Số ngày còn lại', compute='_compute_days_remaining')

    @api.depends('expiry_date')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for record in self:
            if record.expiry_date:
                delta = record.expiry_date - today
                record.days_remaining = delta.days
            else:
                record.days_remaining = 0

    # Cập nhật trạng thái dựa trên ngày hết hạn
    @api.model
    def _update_certification_states(self):
        today = fields.Date.today()
        expiring_date = today + timedelta(days=30)

        # Cập nhật chứng nhận sắp hết hạn
        expiring_certs = self.search([
            ('expiry_date', '<=', expiring_date),
            ('expiry_date', '>', today),
            ('state', '=', 'valid')
        ])
        expiring_certs.write({'state': 'expiring'})

        # Cập nhật chứng nhận đã hết hạn
        expired_certs = self.search([
            ('expiry_date', '<', today),
            ('state', 'in', ['valid', 'expiring'])
        ])
        expired_certs.write({'state': 'expired'})

        # Gửi email nhắc nhở
        self._send_expiry_reminders()

        return True

    def _send_expiry_reminders(self):
        today = fields.Date.today()
        for cert in self.search([('renewal_reminder', '=', True)]):
            if cert.expiry_date and cert.responsible_id and cert.reminder_days:
                reminder_date = cert.expiry_date - timedelta(days=cert.reminder_days)
                if reminder_date <= today and cert.state != 'expired':
                    template = self.env.ref('hospital_certification.mail_template_certification_reminder')
                    if template:
                        template.send_mail(cert.id, force_send=True)

    # Hành động gia hạn
    def action_renew(self):
        self.ensure_one()
        return {
            'name': _('Gia hạn chứng nhận'),
            'view_mode': 'form',
            'res_model': 'hospital.certification.renew.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {'default_certification_id': self.id},
            'target': 'new'
        }

    # Cập nhật trạng thái
    def action_set_valid(self):
        self.write({'state': 'valid'})

    def action_set_draft(self):
        self.write({'state': 'draft'})


class CertificationRenewWizard(models.TransientModel):
    _name = 'hospital.certification.renew.wizard'
    _description = 'Wizard gia hạn chứng nhận'

    certification_id = fields.Many2one('hospital.certification', string='Chứng nhận', required=True)
    current_expiry_date = fields.Date(related='certification_id.expiry_date', string='Ngày hết hạn hiện tại')
    new_expiry_date = fields.Date(string='Ngày hết hạn mới', required=True)
    renewal_document = fields.Binary(string='Tài liệu gia hạn')
    renewal_document_filename = fields.Char(string='Tên file tài liệu gia hạn')
    notes = fields.Text(string='Ghi chú')

    @api.onchange('certification_id')
    def _onchange_certification_id(self):
        if self.certification_id and self.certification_id.expiry_date:
            self.new_expiry_date = self.certification_id.expiry_date + timedelta(days=365)

    def action_confirm_renewal(self):
        self.ensure_one()
        if self.new_expiry_date <= self.current_expiry_date:
            raise UserError(_('Ngày hết hạn mới phải sau ngày hết hạn hiện tại!'))

        # Tạo bản ghi kiểm tra mới
        inspection_vals = {
            'name': _('Gia hạn - %s') % self.certification_id.name,
            'certification_id': self.certification_id.id,
            'date': fields.Date.today(),
            'result': 'passed',
            'notes': self.notes or _('Gia hạn chứng nhận từ %s đến %s') %
                     (self.current_expiry_date, self.new_expiry_date),
            'document': self.renewal_document,
            'document_filename': self.renewal_document_filename,
            'inspector': self.env.user.name,
        }
        self.env['hospital.inspection'].create(inspection_vals)

        # Cập nhật chứng nhận
        self.certification_id.write({
            'expiry_date': self.new_expiry_date,
            'state': 'valid',
            'renewal_date': self.new_expiry_date,
        })

        return {'type': 'ir.actions.act_window_close'}
