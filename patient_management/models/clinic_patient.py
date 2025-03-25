from odoo import models, fields, api
from datetime import datetime, date
from odoo.exceptions import ValidationError
import uuid


class ClinicPatient(models.Model):
    _name = 'clinic.patient'
    _description = 'Thông tin bệnh nhân'
    _rec_name = 'code'
    _order = "date desc"

    code = fields.Char(
        string='Mã bệnh nhân',
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )
    name = fields.Char(
        string="Họ và tên",
        required=True,
    )
    email = fields.Char(
        string="Email"
    )
    gender = fields.Selection(
        string="Giới tính",
        selection=[
            ('male', 'Nam'),
            ('female', 'Nữ'),
            ('other', 'Khác')
        ],
        required=True,
        default="other"
    )
    age = fields.Integer(
        string="Tuổi",
        compute="_compute_age",
    )
    date_of_birth = fields.Date(
        string="Ngày sinh",
    )
    phone = fields.Char(
        string="Số điện thoại",
    )
    date = fields.Datetime(
        string="Ngày đăng ký",
        default=datetime.now(),
        required=True,
    )
    patient_type = fields.Selection(
        [
            ('outpatient', 'Ngoại trú'),
            ('inpatient', 'Nội trú')
        ],
        string='Loại bệnh nhân',
        required=True,
        default='outpatient',
        readonly=True)
    note = fields.Text(string='Ghi chú')

    insurance_number = fields.Char(string='Số thẻ BHYT', compute='_compute_insurance_info')
    insurance_facility = fields.Char(string='Nơi ĐKKCB', compute='_compute_insurance_info')
    insurance_expiry = fields.Date(c='Có giá trị đến', compute='_compute_insurance_info')
    insurance_tier = fields.Selection([
        ('central', 'Trung ương'),
        ('province', 'Tỉnh'),
        ('district', 'Quận/Huyện'),
        ('commune', 'Xã')
    ], string='Tuyến', compute='_compute_insurance_info')
    insurance_state = fields.Char(string='Trạng thái', compute='_compute_insurance_info')
    has_insurance = fields.Boolean(string='Có bảo hiểm', compute='_compute_insurance_info')

    # dùng cái hàm này để tìm kiếm bảo hiểm của bệnh nhân
    @api.depends('name')
    def _compute_insurance_info(self):
        for patient in self:
            insurance = self.env['clinic.insurance.policy'].search([
                ('patient_id', '=', patient.id)
            ], limit=1)

            if insurance:
                patient.has_insurance = True
                patient.insurance_number = insurance.number
                patient.insurance_facility = insurance.facility
                patient.insurance_tier = insurance.tier
                patient.insurance_expiry = insurance.expiry_date
                if insurance.state == 'valid':
                    patient.insurance_state = 'Hợp lệ'
                else:
                    patient.insurance_state = 'Hết hạn'
            else:
                patient.has_insurance = False
                patient.insurance_number = False
                patient.insurance_facility = False
                patient.insurance_tier = False
                patient.insurance_expiry = False
                patient.insurance_state = False

    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            today = date.today()
            if record.date_of_birth:
                record.age = today.year - record.date_of_birth.year
            else:
                record.age = 0

    def action_hospitalize(self):
        """Cập nhật trạng thái thành 'Đang nhập viện' khi nhấn nút trong form."""
        self.write({'state': 'hospitalized'})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                # Generate a short UUID
                vals['code'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

    # def get_insurance_info(self):
    #     for patient in self:
    #         # Search for insurance records linked to this patient
    #         insurance_records = self.env['clinic.insurance.policy'].search([
    #             ('patient_id', '=', patient.id)
    #         ])

    #         print(f"Insurance information for {patient.patient_name}:")
    #         for insurance in insurance_records:
    #             print(f"  - Insurance Number: {insurance.number}")
    #             print(f"  - Facility: {insurance.facility}")
    #             print(f"  - Expiry Date: {insurance.expiry_date}")
    #             print(f"  - State: {insurance.state}")
