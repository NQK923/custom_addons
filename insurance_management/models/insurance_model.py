from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class ClinicPatientInsurance(models.Model):
    _name = 'clinic.insurance.policy'
    _description = 'Thông tin bảo hiểm y tế'

    insurance_id = fields.Char(string='Mã bảo hiểm', required=True, readonly=True, default='New')
    number = fields.Char(string='Số thẻ BHYT', required=True, unique=True)
    facility = fields.Char(string='Nơi ĐKKCB', required=True)
    tier = fields.Selection([
        ('central', 'Trung ương'),
        ('province', 'Tỉnh'),
        ('district', 'Quận/Huyện'),
        ('commune', 'Xã')
    ], string='Tuyến', required=True)
    expiry_date = fields.Date(string='Thời hạn', required=True)
    state = fields.Selection([
        ('valid', 'Hợp lệ'),
        ('expired', 'Hết hạn')
    ], string='Trạng thái', compute='_compute_state', store=True)
    
    # Sửa lại định nghĩa quan hệ
    # patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True, ondelete='restrict')
    
    # _sql_constraints = [
    #     ('unique_patient', 'unique(patient_id)', 'Bệnh nhân này đã có bảo hiểm y tế!')
    # ]

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

    @api.model
    def create(self, vals):
        if vals.get('insurance_id', 'New') == 'New':
            vals['insurance_id'] = self.env['ir.sequence'].next_by_code('clinic.insurance.sequence') or 'IS-0001'
        return super(ClinicPatientInsurance, self).create(vals)

