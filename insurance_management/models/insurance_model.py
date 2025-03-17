from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class ClinicPatientInsurance(models.Model):
    _name = 'clinic.insurance.policy'
    _description = 'Thông tin bảo hiểm y tế của bệnh nhân'

    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True, ondelete='cascade')
    insurance_number = fields.Char(string='Số thẻ BHYT', required=True, unique=True)
    insurance_initial_facility = fields.Char(string='Nơi ĐKKCB', required=True)
    insurance_tier = fields.Selection([
        ('central', 'Trung ương'),
        ('province', 'Tỉnh'),
        ('district', 'Quận/Huyện'),
        ('commune', 'Xã')
    ], string='Tuyến', required=True)
    insurance_expiry_date = fields.Date(string='Thời hạn', required=True)
    insurance_state = fields.Selection([
        ('valid', 'Hợp lệ'),
        ('expired', 'Hết hạn')
    ], string='Trạng thái', compute='_compute_state', store=True)

    @api.depends('insurance_expiry_date')
    def _compute_state(self):
        today = date.today()
        for record in self:
            if not record.insurance_expiry_date:
                record.insurance_state = 'valid'  # Hoặc để trống tùy nghiệp vụ
            elif record.insurance_expiry_date < today:
                record.insurance_state = 'expired'
            else:
                record.insurance_state = 'valid'

    @api.constrains('insurance_number')
    def _check_insurance_number_length(self):
        for record in self:
            if len(record.insurance_number) != 15:  # Giả định số thẻ BHYT là 15 ký tự
                raise ValidationError("Số thẻ BHYT phải có đúng 15 ký tự!")

    class ClinicPatient(models.Model):
        _name = 'clinic.patient'
        _description = 'Thông tin bệnh nhân'

        name = fields.Char(string='Họ và tên', required=True)
        gender = fields.Selection([
            ('male', 'Nam'),
            ('female', 'Nữ'),
            ('other', 'Khác')
        ], string='Giới tính', required=True)
        phone = fields.Char(string='Số điện thoại', required=True)
        address = fields.Text(string='Địa chỉ')
        insurance_policy_id = fields.Many2one('clinic.insurance.policy', string='Bảo hiểm y tế')
