import re
import uuid
from datetime import datetime, date

from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    email_normalized = fields.Char(
        string="Email chuẩn hóa",
        compute="_compute_normalized_values",
        store=True,
        index=True,
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
    phone_normalized = fields.Char(
        string="SĐT chuẩn hóa",
        compute="_compute_normalized_values",
        store=True,
        index=True,
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

    # Thêm ràng buộc SQL cấp cơ sở dữ liệu
    _sql_constraints = [
        ('email_normalized_unique', 'unique(email_normalized)',
         'Email này đã được sử dụng cho bệnh nhân khác!'),
        ('phone_normalized_unique', 'unique(phone_normalized)',
         'Số điện thoại này đã được sử dụng cho bệnh nhân khác!'),
    ]

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} - {record.name}"

    @api.depends('email', 'phone')
    def _compute_normalized_values(self):
        """Chuẩn hóa email và SĐT để đảm bảo tính duy nhất"""
        for record in self:
            # Chuẩn hóa email
            if record.email:
                email = record.email.strip().lower()
                record.email_normalized = email
            else:
                record.email_normalized = False

            # Chuẩn hóa số điện thoại (loại bỏ khoảng trắng và ký tự đặc biệt)
            if record.phone:
                # Loại bỏ tất cả các ký tự không phải số
                phone = re.sub(r'\D', '', record.phone)
                record.phone_normalized = phone
            else:
                record.phone_normalized = False

    @api.constrains('email', 'email_normalized')
    def _check_email_unique(self):
        for record in self:
            if record.email_normalized:
                same_email = self.env['clinic.patient'].search([
                    ('email_normalized', '=', record.email_normalized),
                    ('id', '!=', record.id)
                ], limit=1)
                if same_email:
                    raise ValidationError(f"Email '{record.email}' đã được sử dụng cho bệnh nhân {same_email.name}!")

    @api.constrains('phone', 'phone_normalized')
    def _check_phone_unique(self):
        for record in self:
            if record.phone_normalized:
                same_phone = self.env['clinic.patient'].search([
                    ('phone_normalized', '=', record.phone_normalized),
                    ('id', '!=', record.id)
                ], limit=1)
                if same_phone:
                    raise ValidationError(
                        f"Số điện thoại '{record.phone}' đã được sử dụng cho bệnh nhân {same_phone.name}!")

    @api.onchange('email')
    def _onchange_email(self):
        """Kiểm tra email khi người dùng thay đổi giá trị"""
        if self.email:
            email = self.email.strip().lower()
            same_email = self.env['clinic.patient'].search([
                ('email_normalized', '=', email),
                ('id', '!=', self.id)
            ], limit=1)
            if same_email:
                return {'warning': {
                    'title': 'Email trùng lặp',
                    'message': f"Email '{self.email}' đã được sử dụng cho bệnh nhân {same_email.name}!",
                }}

    @api.onchange('phone')
    def _onchange_phone(self):
        """Kiểm tra SĐT khi người dùng thay đổi giá trị"""
        if self.phone:
            phone = re.sub(r'\D', '', self.phone)
            same_phone = self.env['clinic.patient'].search([
                ('phone_normalized', '=', phone),
                ('id', '!=', self.id)
            ], limit=1)
            if same_phone:
                return {'warning': {
                    'title': 'Số điện thoại trùng lặp',
                    'message': f"Số điện thoại '{self.phone}' đã được sử dụng cho bệnh nhân {same_phone.name}!",
                }}

    def _compute_insurance_info(self):
        for patient in self:
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
