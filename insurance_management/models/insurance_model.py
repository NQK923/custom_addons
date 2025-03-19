from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
import re

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
    expiry_date = fields.Date(string='Có giá trị đến', required=True)
    state = fields.Selection([
        ('valid', 'Hợp lệ'),
        ('expired', 'Hết hạn')
    ], string='Trạng thái', compute='_compute_state', store=True, tracking=True)

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
            # Kiểm tra định dạng: 2 chữ cái + 1 số + 2 số + 10 số
            pattern = r'^[A-Z]{2}[1-5][0-9]{2}[0-9]{10}$'
            if not re.match(pattern, record.number):
                raise ValidationError('''Số thẻ BHYT không hợp lệ! 
                    Định dạng phải là: 
                    - 2 chữ cái in hoa (mã đối tượng)
                    - 1 chữ số từ 1-5 (mức hưởng)
                    - 2 chữ số (mã tỉnh)
                    - 10 chữ số (số định danh)
                    Ví dụ: DN119123456789''')
            
            duplicate = self.search([
                ('id', '!=', record.id),
                ('number', '=', record.number)
            ])
            if duplicate:
                raise ValidationError(f'Số thẻ BHYT {record.number} đã tồn tại!')

    @api.model
    def _get_next_sequence(self):
        """Lấy sequence mã bảo hiểm tiếp theo"""
        return self.env['ir.sequence'].next_by_code('clinic.insurance.sequence') or 'New'

    @api.model_create_multi
    def create(self, vals_list):
        """Gán sequence khi tạo record mới, chỉ gán khi tạo thành công"""
        result = super(ClinicInsurance, self).create(vals_list)
        # Sau khi create thành công, mới gán sequence
        for record in result:
            if record.name == 'New':
                sequence = self._get_next_sequence()
                record.name = sequence
        return result

    # Ghi đè cả write để xử lý các trường hợp sao chép
    def copy(self, default=None):
        default = dict(default or {})
        default.update(name='New')
        return super().copy(default)

