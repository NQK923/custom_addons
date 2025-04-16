import re
import uuid

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicInsurance(models.Model):
    _name = 'clinic.insurance.policy'
    _description = 'Thông tin bảo hiểm y tế'
    _rec_name = 'number'

    name = fields.Char(string='Mã bảo hiểm', required=True, copy=False, readonly=True)
    number = fields.Char(string='Số thẻ BHYT', required=True)
    facility = fields.Char(string='Nơi ĐKKCB')
    patient_id = fields.Many2one(
        'clinic.patient',
        string='Bệnh nhân',
        required=True,
        ondelete='restrict'
    )
    expiry_date = fields.Date(string='Có giá trị đến', required=True)
    state = fields.Selection([
        ('valid', 'Hợp lệ'),
        ('expired', 'Hết hạn')
    ], string='Trạng thái', compute='_compute_state', store=True, tracking=True)
    coverage_rate = fields.Selection([
        ('80', '80%'),
        ('95', '95%'),
        ('100', '100%')
    ], string='Mức chi trả', default='100', required=True)

    _sql_constraints = [
        ('unique_patient', 'unique(patient_id)', 'Bệnh nhân này đã có bảo hiểm y tế!'),
        ('number_unique',
         'UNIQUE(number)',
         'Số thẻ BHYT đã tồn tại!')
    ]

    @api.depends('expiry_date')
    def _compute_state(self):
        today = fields.Date.today()
        for record in self:
            if record.expiry_date:
                record.state = 'valid' if record.expiry_date >= today else 'expired'
            else:
                record.state = 'valid'

    @api.constrains('number')
    def _check_number(self):
        for record in self:
            # Kiểm tra định dạng: 10 số
            pattern = r'^[0-9]{10}$'
            if not re.match(pattern, record.number):
                raise ValidationError('''Số thẻ BHYT không hợp lệ! 
                    Định dạng phải là 10 chữ số
                    Ví dụ: 0123456789''')

            duplicate = self.search([
                ('id', '!=', record.id),
                ('number', '=', record.number)
            ])
            if duplicate:
                raise ValidationError(f'Số thẻ BHYT {record.number} đã tồn tại!')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                # Generate a short UUID
                vals['name'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

    # Ghi đè cả write để xử lý các trường hợp sao chép
    def copy(self, default=None):
        default = dict(default or {})
        default.update(name='New')
        return super().copy(default)
