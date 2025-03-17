from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta, date


class ClinicPatient(models.Model):
    _name = 'clinic.patient'
    _description = 'Thông tin bệnh nhân'

    name = fields.Char(string='Họ và Tên', required=True)
    date_of_birth = fields.Date(string='Ngày sinh')
    age = fields.Integer(string='Tuổi', compute='_compute_age', store=True)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', required=True)
    phone = fields.Char(string='Số điện thoại')
    address = fields.Text(string='Địa chỉ')
    patient_type = fields.Selection([
        ('outpatient', 'Ngoại trú'),
        ('inpatient', 'Nội trú')
    ], string='Loại bệnh nhân', required=True, default='outpatient')
    state = fields.Selection([
        ('under_treatment', 'Đang điều trị'),
        ('treated', 'Đã điều trị'),
        ('deceased', 'Tử vong')
    ], string='Trạng thái', default='under_treatment')
    last_activity_date = fields.Datetime(string='Ngày hoạt động gần nhất', default=fields.Datetime.now)
    note = fields.Text(string='Ghi chú')
    insurance = fields.Many2one('clinic.patient.insurance', string='Thông tin bảo hiểm', ondelete='set null')
    insurance_number = fields.Char(string='Số thẻ BHYT', readonly=True, related='insurance.insurance_number')
    initial_facility = fields.Char(string='Nơi ĐKKCB', readonly=True, related='insurance.initial_facility')
    tier = fields.Selection([
        ('central', 'Trung ương'),
        ('province', 'Tỉnh'),
        ('district', 'Quận/Huyện'),
        ('commune', 'Xã')
    ], string='Tuyến', readonly=True, related='insurance.tier')
    expiry_date = fields.Date(string='Thời hạn', readonly=True, related='insurance.expiry_date')
    has_valid_insurance = fields.Boolean(string='Có bảo hiểm hợp lệ', compute='_compute_has_valid_insurance')
    insurance_status = fields.Char(string='BHYT', compute='_compute_insurance_status')

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

    def action_treated(self):
        """Cập nhật trạng thái thành 'Đã điều trị' khi nhấn nút trong form."""
        self.write({'state': 'treated'})
        return True

    def action_deceased(self):
        self.write({'state': 'deceased'})
        return True

    def _check_abandoned_outpatients(self):
        """Cron job để tự động chuyển trạng thái 'under_treatment' thành 'treated' cho bệnh nhân ngoại trú sau 24h."""
        today = fields.Datetime.now()
        threshold = timedelta(hours=24)
        outpatients = self.search([
            ('state', '=', 'under_treatment'),
            ('patient_type', '=', 'outpatient'),
            ('last_activity_date', '<=', today - threshold)
        ])
        for patient in outpatients:
            patient.write({
                'state': 'treated',
                'note': f"{patient.note or ''}\nTự động chuyển thành 'Đã điều trị' sau 24h không hoạt động."
            })

    @api.model
    def _register_hook(self):
        """Đăng ký cron job khi module được cài đặt."""
        cron_name = 'Check Abandoned Outpatients'
        cron_exists = self.env['ir.cron'].search([('name', '=', cron_name)], limit=1)
        if not cron_exists:
            self.env['ir.cron'].create({
                'name': cron_name,
                'model_id': self.env.ref('patient_management.model_clinic_patient').id,
                'state': 'code',
                'code': 'model._check_abandoned_outpatients()',
                'interval_number': 1,
                'interval_type': 'hours',
                'active': True,
            })

    @api.depends('insurance')
    def _compute_has_valid_insurance(self):
        for record in self:
            record.has_valid_insurance = bool(record.insurance and record.insurance.state == 'valid')

    @api.depends('has_valid_insurance')
    def _compute_insurance_status(self):
        for record in self:
            record.insurance_status = 'Có' if record.has_valid_insurance else 'Không có'

    def action_add_insurance(self):
        # Logic để tạo bản ghi bảo hiểm mới
        insurance = self.env['clinic.patient.insurance'].create({
            'insurance_number': 'TEMP_NUMBER',  # Thay bằng logic thực tế
            'initial_facility': 'Some Facility',
            'tier': 'district',
            'expiry_date': date.today() + timedelta(days=365),
        })
        self.write({'insurance': insurance.id})
        return True
