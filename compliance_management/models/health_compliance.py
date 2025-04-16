# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models


class HealthRegulation(models.Model):
    _name = 'health.regulation'
    _description = 'Quy định Y tế'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên quy định', required=True, tracking=True)
    code = fields.Char('Mã quy định', required=True, tracking=True)
    description = fields.Text('Mô tả')
    issue_date = fields.Date('Ngày ban hành', tracking=True)
    effective_date = fields.Date('Ngày có hiệu lực', tracking=True)
    authority_id = fields.Many2one('health.authority', string='Cơ quan ban hành', tracking=True)
    scope = fields.Selection([
        ('national', 'Quốc gia'),
        ('international', 'Quốc tế'),
        ('local', 'Địa phương')
    ], string='Phạm vi', default='national', tracking=True)
    compliance_ids = fields.One2many('health.compliance', 'regulation_id', string='Đánh giá tuân thủ')
    attachment_ids = fields.Many2many('ir.attachment', string='Tài liệu đính kèm')
    active = fields.Boolean(default=True)


class HealthAuthority(models.Model):
    _name = 'health.authority'
    _description = 'Cơ quan quản lý y tế'

    name = fields.Char('Tên cơ quan', required=True)
    code = fields.Char('Mã cơ quan')
    country_id = fields.Many2one('res.country', string='Quốc gia')
    description = fields.Text('Mô tả')
    regulation_ids = fields.One2many('health.regulation', 'authority_id', string='Quy định')


class HealthCompliance(models.Model):
    _name = 'health.compliance'
    _description = 'Đánh giá tuân thủ'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên đánh giá', required=True, tracking=True)
    regulation_id = fields.Many2one('health.regulation', string='Quy định', required=True, tracking=True)
    department_id = fields.Many2one('clinic.department', string='Phòng ban', tracking=True)
    date_assessment = fields.Date('Ngày đánh giá', default=fields.Date.today, tracking=True)
    next_assessment = fields.Date('Đánh giá tiếp theo', tracking=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('in_progress', 'Đang thực hiện'),
        ('compliant', 'Tuân thủ'),
        ('non_compliant', 'Không tuân thủ'),
        ('partly_compliant', 'Tuân thủ một phần')
    ], string='Trạng thái', default='draft', tracking=True)
    responsible_id = fields.Many2one('res.users', string='Người phụ trách', default=lambda self: self.env.user,
                                     tracking=True)
    notes = fields.Text('Ghi chú')
    action_ids = fields.One2many('health.compliance.action', 'compliance_id', string='Hành động khắc phục')
    attachment_ids = fields.Many2many('ir.attachment', string='Tài liệu đính kèm')

    @api.onchange('regulation_id')
    def _onchange_regulation_id(self):
        if self.regulation_id:
            self.name = f"Đánh giá tuân thủ - {self.regulation_id.name}"

    @api.model
    def create(self, vals):
        if not vals.get('next_assessment') and vals.get('date_assessment'):
            assessment_date = fields.Date.from_string(vals.get('date_assessment'))
            vals['next_assessment'] = assessment_date + timedelta(days=90)
        return super(HealthCompliance, self).create(vals)


class HealthComplianceAction(models.Model):
    _name = 'health.compliance.action'
    _description = 'Hành động khắc phục'

    name = fields.Char('Tên hành động', required=True)
    compliance_id = fields.Many2one('health.compliance', string='Đánh giá tuân thủ')
    description = fields.Text('Mô tả')
    deadline = fields.Date('Hạn chót')
    responsible_id = fields.Many2one('res.users', string='Người phụ trách')
    state = fields.Selection([
        ('todo', 'Cần thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Hủy bỏ')
    ], string='Trạng thái', default='todo')
    completion_date = fields.Date('Ngày hoàn thành')
    notes = fields.Text('Ghi chú')
