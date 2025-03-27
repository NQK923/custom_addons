from odoo import models, fields, api
from datetime import datetime, date
from odoo.exceptions import ValidationError
import uuid

# Model ClinicPatient
class ClinicPatient(models.Model):
    _name = 'clinic.patient'
    _description = 'Thông tin bệnh nhân'
    _rec_name = 'code'
    _order = "date desc"

    code = fields.Char(string='Mã bệnh nhân', required=True, copy=False, readonly=True, default="New")
    name = fields.Char(string="Họ và tên", required=True)
    email = fields.Char(string="Email")
    gender = fields.Selection(
        string="Giới tính",
        selection=[('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')],
        required=True,
        default="other"
    )
    age = fields.Integer(string="Tuổi", compute="_compute_age")
    date_of_birth = fields.Date(string="Ngày sinh")
    phone = fields.Char(string="Số điện thoại")
    date = fields.Datetime(string="Ngày đăng ký", default=datetime.now(), required=True)
    patient_type = fields.Selection(
        [('outpatient', 'Ngoại trú'), ('inpatient', 'Nội trú')],
        string='Loại bệnh nhân',
        required=True,
        default='outpatient',
        readonly=True
    )
    note = fields.Text(string='Ghi chú')
    insurance_number = fields.Char(string='Số thẻ BHYT', compute='_compute_insurance_info')
    insurance_facility = fields.Char(string='Nơi ĐKKCB', compute='_compute_insurance_info')
    insurance_expiry = fields.Date(string='Có giá trị đến', compute='_compute_insurance_info')
    insurance_tier = fields.Selection(
        [('central', 'Trung ương'), ('province', 'Tỉnh'), ('district', 'Quận/Huyện'), ('commune', 'Xã')],
        string='Tuyến',
        compute='_compute_insurance_info'
    )
    insurance_state = fields.Char(string='Trạng thái', compute='_compute_insurance_info')
    has_insurance = fields.Boolean(string='Có bảo hiểm', compute='_compute_insurance_info')
    medical_history_ids = fields.One2many('patient.medical.history', 'patient_id', string='Lịch sử y tế')
    treatment_plan_ids = fields.One2many('treatment.plan', 'patient_id', string='Kế hoạch điều trị')  # Thêm trường này

    @api.depends('name')
    def _compute_insurance_info(self):
        for patient in self:
            insurance = self.env['clinic.insurance.policy'].search([('patient_id', '=', patient.id)], limit=1)
            if insurance:
                patient.has_insurance = True
                patient.insurance_number = insurance.number
                patient.insurance_facility = insurance.facility
                patient.insurance_tier = insurance.tier
                patient.insurance_expiry = insurance.expiry_date
                patient.insurance_state = 'Hợp lệ' if insurance.state == 'valid' else 'Hết hạn'
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

# Model TreatmentPlan
class TreatmentPlan(models.Model):
    _name = 'treatment.plan'
    _description = 'Treatment Plan'

    code = fields.Char(string='Mã kế hoạch điều trị', required=True)
    patient_id = fields.Many2one('clinic.patient', string='Mã bệnh nhân', required=True)
    start_date = fields.Date(string='Ngày bắt đầu', required=True)
    end_date = fields.Date(string='Ngày kết thúc')
    treatment_process_ids = fields.One2many('treatment.process', 'plan_id', string='Quá trình điều trị')

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('treatment.plan') or '1'
        return super().create(vals)

# Model TreatmentProcess
class TreatmentProcess(models.Model):
    _name = 'treatment.process'
    _description = 'Treatment Process'

    code = fields.Char(string='Mã quá trình', required=True)
    plan_id = fields.Many2one('treatment.plan', string='Kế hoạch điều trị', required=True, ondelete='cascade')
    service_id = fields.Many2one('clinic.service', string='Loại dịch vụ', required=True)
    executor_id = fields.Many2one('clinic.staff', string='Người thực hiện', required=True)
    state = fields.Selection(
        [('pending', 'Chưa thực hiện'), ('in_progress', 'Đang thực hiện'), ('completed', 'Hoàn thành')],
        string='Trạng thái', default='pending', required=True
    )
    execution_time = fields.Datetime(string='Thời gian thực hiện')
    prescription_id = fields.Many2one('prescription.order', string='Mã đơn thuốc')

    @api.model
    def create(self, vals):
        if not vals.get('executor_id'):
            raise ValidationError("Người thực hiện không được để trống.")
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('treatment.process') or '1'
        return super().create(vals)

    def write(self, vals):
        if 'executor_id' in vals and not vals['executor_id']:
            raise ValidationError("Người thực hiện không được để trống.")
        return super().write(vals)

# Model MedicalTest
class MedicalTest(models.Model):
    _name = 'medical.test'
    _description = 'Medical Test Management'

    test_code = fields.Char(string='Mã xét nghiệm và chuẩn đoán', required=True)
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True)
    test_type = fields.Selection(
        [('test', 'Chuẩn đoán'), ('blood', 'Máu'), ('urine', 'Nước tiểu'), ('xray', 'X-Quang'), ('ecg', 'ECG'), ('other', 'Khác')],
        string='Loại xét nghiệm hoặc chuẩn đoán', required=True
    )
    test_date = fields.Datetime(string='Ngày thực hiện', required=True)
    status = fields.Selection(
        [('request', 'Yêu cầu'), ('processing', 'Đang xử lý'), ('completed', 'Hoàn tất')],
        string='Trạng thái', default='request'
    )
    result = fields.Text(string='Kết quả xét nghiệm hoặc chuẩn đoán')
    medical_images = fields.One2many('medical.images', 'MedicalTest_id', string='Hình ảnh y tế')

# Model MedicalImages
class MedicalImages(models.Model):
    _name = 'medical.images'
    _description = 'Medical Images'

    test_code = fields.Char(string='Mã hình ảnh xét nghiệm', required=True, copy=False)
    MedicalTest_id = fields.Many2one('medical.test', string='Mã xét nghiệm', required=True)
    test_type_img = fields.Selection(
        [('test', 'Chuẩn đoán'), ('blood', 'Máu'), ('urine', 'Nước tiểu'), ('xray', 'X-Quang'), ('ecg', 'ECG'), ('other', 'Khác')],
        string='Loại xét nghiệm hoặc chuẩn đoán', required=True
    )
    img_date = fields.Datetime(string='Ngày thực hiện', required=True)
    result_Img = fields.Text(string='Kết quả chuẩn đoán hoặc xét nghiệm')
    Img = fields.Binary(string='Hình ảnh', attachment=True)

    @api.model
    def create(self, vals):
        last_record = self.search([], order='id desc', limit=1)
        next_code = int(last_record.test_code) + 1 if last_record and last_record.test_code.isdigit() else 1
        vals['test_code'] = str(next_code)
        return super().create(vals)

# Model PatientCareTracking
class PatientCareTracking(models.Model):
    _name = 'patient.care.tracking'
    _description = 'Patient Care Tracking'

    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True, ondelete='cascade')
    tracking_date = fields.Datetime(string='Ngày theo dõi', default=fields.Datetime.now)
    note = fields.Text(string='Ghi chú')

# Model PatientMedicalHistory
class PatientMedicalHistory(models.Model):
    _name = 'patient.medical.history'
    _description = 'Patient Medical History'

    patient_id = fields.Many2one('clinic.patient', string='Mã bệnh nhân', required=True, ondelete='cascade')
    history_date = fields.Datetime(string='Ngày ghi nhận', default=fields.Datetime.now)
    medical_tests = fields.One2many('medical.test', 'patient_id', string='Xét nghiệm', readonly=True)
    medical_images = fields.One2many('medical.images', 'MedicalTest_id', string='Hình ảnh y tế', compute='_compute_medical_images', readonly=True)
    treatment_plans = fields.One2many('treatment.plan', 'patient_id', string='Kế hoạch điều trị', readonly=True)
    treatment_processes = fields.One2many('treatment.process', 'plan_id', string='Quá trình điều trị', compute='_compute_treatment_processes', readonly=True)
    care_trackings = fields.One2many('patient.care.tracking', 'patient_id', string='Theo dõi chăm sóc', readonly=True)

    @api.depends('medical_tests')
    def _compute_medical_images(self):
        for record in self:
            test_ids = record.medical_tests.mapped('id')
            record.medical_images = self.env['medical.images'].search([('MedicalTest_id', 'in', test_ids)])

    @api.depends('treatment_plans')
    def _compute_treatment_processes(self):
        for record in self:
            plan_ids = record.treatment_plans.mapped('id')
            record.treatment_processes = self.env['treatment.process'].search([('plan_id', 'in', plan_ids)])