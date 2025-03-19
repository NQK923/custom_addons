from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class ClinicPatient(models.Model):
    _name = 'clinic.patient'
    _description = 'Thông tin bệnh nhân'

    patient_id = fields.Char(string='Mã bệnh nhân', required=True, readonly=True, default='New')
    name = fields.Char(string='Họ và Tên', required=True)
    date_of_birth = fields.Date(string='Ngày sinh')
    age = fields.Integer(string='Tuổi', compute='_compute_age', store=True)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', required=True)
    phone = fields.Char(string='Số điện thoại')
    email = fields.Char(string='Địa chỉ email')
    address = fields.Text(string='Địa chỉ')
    patient_type = fields.Selection([
        ('outpatient', 'Ngoại trú'),
        ('inpatient', 'Nội trú')
    ], string='Loại bệnh nhân', required=True, default='outpatient')
    state = fields.Selection([
        ('registered', 'Đã đăng ký'),
        ('hospitalized', 'Đang nhập viện')
    ], string='Trạng thái', default='registered')
    note = fields.Text(string='Ghi chú')

    # Sửa lại định nghĩa quan hệ
    # insurance_id = fields.One2many('clinic.insurance.policy', 'patient_id', string='Bảo hiểm y tế')
    # has_insurance = fields.Boolean(string='Có BHYT', compute='_compute_has_insurance', store=True)

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.today()
        for record in self:
            if record.date_of_birth:
                birth_date = fields.Date.from_string(record.date_of_birth)
                record.age = today.year - birth_date.year - (
                        (today.month, today.day) < (birth_date.month, birth_date.day))
            else:
                record.age = 0

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for record in self:
            if record.date_of_birth and record.date_of_birth > fields.Date.today():
                raise ValidationError("Ngày sinh không thể là ngày trong tương lai!")

    def action_hospitalize(self):
        """Cập nhật trạng thái thành 'Đang nhập viện' khi nhấn nút trong form."""
        self.write({'state': 'hospitalized'})
        return True


    # @api.model
    # def create(self, vals):
    #     if vals.get('patient_id', 'New') == 'New':
    #         vals['patient_id'] = self.env['ir.sequence'].next_by_code('clinic.patient.sequence') or 'P-0001'
    #     return super(ClinicPatient, self).create(vals)

    # @api.depends('insurance_id')
    # def _compute_has_insurance(self):
    #     for record in self:
    #         record.has_insurance = bool(record.insurance_id)
