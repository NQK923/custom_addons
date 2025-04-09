from odoo import models, fields, api
from datetime import datetime, date
from odoo.exceptions import ValidationError
import uuid


class ClinicPatient(models.Model):
    _name = 'clinic.patient'
    _description = 'Thông tin bệnh nhân'
    _rec_name = 'display_name'
    _order = "date desc"

    display_name = fields.Char(
        compute='_compute_display_name',
    )
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
    insurance_coverage_rate = fields.Selection([
        ('80', '80%'),
        ('95', '95%'),
        ('100', '100%')
    ], string='Mức chi trả', compute='_compute_insurance_info')
    insurance_state = fields.Char(string='Trạng thái', compute='_compute_insurance_info')
    has_insurance = fields.Boolean(string='Có bảo hiểm', compute='_compute_insurance_info')

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} - {record.name}"

    @api.constrains('email')
    def _check_email_unique(self):
        for record in self:
            if record.email:  # Chỉ kiểm tra nếu email không trống
                same_email = self.env['clinic.patient'].search([
                    ('email', '=', record.email),
                    ('id', '!=', record.id)
                ])
                if same_email:
                    raise ValidationError(f"Email '{record.email}' đã được sử dụng cho bệnh nhân {same_email[0].name}!")

    @api.constrains('phone')
    def _check_phone_unique(self):
        for record in self:
            if record.phone:  # Chỉ kiểm tra nếu số điện thoại không trống
                same_phone = self.env['clinic.patient'].search([
                    ('phone', '=', record.phone),
                    ('id', '!=', record.id)
                ])
                if same_phone:
                    raise ValidationError(
                        f"Số điện thoại '{record.phone}' đã được sử dụng cho bệnh nhân {same_phone[0].name}!")

    def _compute_insurance_info(self):
        # InsuranceModel = self.env.get('clinic.insurance.policy', False)
        for patient in self:
            # if not InsuranceModel:
            #     # Nếu module bảo hiểm không tồn tại, xóa các trường bảo hiểm
            #     print(f"No module insurance")
            #     patient._clear_insurance_fields()
            #     continue
            # Tìm bản ghi bảo hiểm liên quan đến bệnh nhân
            # insurance = InsuranceModel.search([
            #     ('patient_id', '=', patient.id)
            # ], limit=1)
            insurance = self.env['clinic.insurance.policy'].search([
                ('patient_id', '=', patient.id)
            ], limit=1)

            if insurance:
                # Nếu có bảo hiểm, cập nhật thông tin
                patient.has_insurance = True
                patient.insurance_number = insurance.number
                patient.insurance_facility = insurance.facility
                patient.insurance_expiry = insurance.expiry_date
                patient.insurance_coverage_rate = insurance.coverage_rate
                patient.insurance_state = 'Hợp lệ' if insurance.state == 'valid' else 'Hết hạn'
            else:
                # Nếu không có bảo hiểm, xóa các trường
                print(f"No insurance information found for {patient.name}")
                patient._clear_insurance_fields()

    def _clear_insurance_fields(self):
        self.has_insurance = False
        self.insurance_number = False
        self.insurance_facility = False
        self.insurance_coverage_rate = False
        self.insurance_expiry = False
        self.insurance_state = False

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