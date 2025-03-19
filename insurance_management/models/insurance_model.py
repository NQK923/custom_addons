from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class ClinicInsurance(models.Model):
    _name = 'clinic.insurance.policy'
    _description = 'Thông tin bảo hiểm y tế'

    name = fields.Char(string='Mã bảo hiểm', required=True, copy=False, readonly=True, default='New')
    number = fields.Char(string='Số thẻ BHYT', required=True)
    facility = fields.Char(string='Nơi ĐKKCB')
    tier = fields.Selection([
        ('central', 'Trung ương'),
        ('province', 'Tỉnh'),
        ('district', 'Quận/Huyện'),
        ('commune', 'Xã')
    ], string='Tuyến', default='district')
    patient_id = fields.Many2one(
        'clinic.patient', 
        string='Bệnh nhân', 
        required=True,
        ondelete='restrict'
    )
    expiry_date = fields.Date(string='Thời hạn')
    state = fields.Selection([
        ('valid', 'Hợp lệ'),
        ('expired', 'Hết hạn')
    ], string='Trạng thái', compute='_compute_state', store=True)

    _sql_constraints = [
        ('unique_patient', 'unique(patient_id)', 'Bệnh nhân này đã có bảo hiểm y tế!')
    ]

    @api.depends('expiry_date')
    def _compute_state(self):
        today = date.today()
        for record in self:
            if not record.expiry_date:
                record.state = 'valid'
            elif record.expiry_date < today:
                record.state = 'expired'
            else:
                record.state = 'valid'

    @api.constrains('number')
    def _check_number_length(self):
        for record in self:
            if len(record.number) != 15:
                raise ValidationError("Số thẻ BHYT phải có đúng 15 ký tự!")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('clinic.insurance.sequence')
        return super().create(vals_list)

