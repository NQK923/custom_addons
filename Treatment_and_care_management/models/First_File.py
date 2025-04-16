from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


# Kế hoạch điều trị
class TreatmentPlan(models.Model):
    _name = 'treatment.plan'
    _description = 'Treatment Plan'

    code = fields.Char(
        string='Mã kế hoạch điều trị',
        required=True
    )
    patient_id = fields.Many2one(
        'clinic.patient',
        string='Mã bệnh nhân',
        required=True
    )
    start_date = fields.Date(string='Ngày bắt đầu', required=True)
    end_date = fields.Date(string='Ngày kết thúc')
    treatment_process_ids = fields.One2many(
        'treatment.process',
        'plan_id',
        string='Quá trình điều trị'
    )

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('treatment.plan') or '1'
        return super(TreatmentPlan, self).create(vals)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_date and record.end_date < record.start_date:
                raise ValidationError("Ngày kết thúc không thể trước ngày bắt đầu!")


class TreatmentProcess(models.Model):
    _name = 'treatment.process'
    _description = 'Treatment Process'

    code = fields.Char(
        string='Mã quá trình',
        required=True
    )
    plan_id = fields.Many2one(
        'treatment.plan',
        string='Kế hoạch điều trị',
        required=True,
        ondelete='cascade'
    )
    service_id = fields.Many2one(
        'clinic.service',
        string='Loại dịch vụ',
        required=True

    )
    executor_id = fields.Many2one(
        'clinic.staff',
        string='Người thực hiện',
        required=True
    )
    state = fields.Selection([
        ('pending', 'Chưa thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành')
    ], string='Trạng thái', default='pending', required=True)
    execution_time = fields.Datetime(string='Thời gian thực hiện')
    prescription_id = fields.Many2one(
        'prescription.order',
        string='Mã đơn thuốc'
    )

    @api.model
    def create(self, vals):
        if not vals.get('executor_id'):
            raise ValidationError("Người thực hiện không được để trống.")
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('treatment.process') or '1'
        return super(TreatmentProcess, self).create(vals)

    def write(self, vals):
        if 'executor_id' in vals and not vals['executor_id']:
            raise ValidationError("Người thực hiện không được để trống.")
        return super(TreatmentProcess, self).write(vals)

    @api.constrains('execution_time', 'plan_id')
    def _check_execution_date(self):
        for record in self:
            if record.execution_time and record.plan_id:
                # Convert datetime to date for comparison
                execution_date = record.execution_time.date()

                # Get plan start and end dates
                plan_start_date = record.plan_id.start_date
                plan_end_date = record.plan_id.end_date

                # Check if execution date is before plan start date
                if execution_date < plan_start_date:
                    raise ValidationError("Thời gian thực hiện không thể trước ngày bắt đầu của kế hoạch điều trị!")

                # Check if execution date is after plan end date (if end date is set)
                if plan_end_date and execution_date > plan_end_date:
                    raise ValidationError("Thời gian thực hiện không thể sau ngày kết thúc của kế hoạch điều trị!")


class PatientCareTracking(models.Model):
    _name = "patient.care.tracking"
    _description = "Theo dõi chăm sóc bệnh nhân"

    patient_id = fields.Many2one(
        'clinic.patient',
        string='Mã bệnh nhân',
        required=True
    )
    care_date = fields.Date(string="Ngày chăm sóc", default=fields.Date.context_today, required=True)
    doctor_id = fields.Many2one('clinic.staff', string="Nhân viên chăm sóc")
    statenew = fields.Selection([
        ('pending', 'Chưa thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành')
    ], string='Trạng thái', default='pending', required=True)

    # Dấu hiệu sinh tồn
    temperature = fields.Float(string="Nhiệt độ (°C)")
    blood_pressure = fields.Char(string="Huyết áp (mmHg)")
    heart_rate = fields.Integer(string="Nhịp tim (bpm)")
    respiration_rate = fields.Integer(string="Tần số hô hấp (lần/phút)")
    oxygen_saturation = fields.Float(string="Độ bão hòa oxy (%)")

    # Chăm sóc đặc biệt
    special_care_description = fields.Text(string="Mô tả chăm sóc đặc biệt")
    medical_equipment_used = fields.Char(string="Thiết bị y tế sử dụng")
    is_emergency = fields.Boolean(string="Khẩn cấp", default=False)

    # Chăm sóc hằng ngày
    daily_nursing_notes = fields.Text(string="Ghi chú chăm sóc hằng ngày")
    abnormal_event = fields.Text(string="Sự kiện bất thường")
    is_alert_triggered = fields.Boolean(string="Đã kích hoạt cảnh báo", default=False)

    # Thông tin người chăm sóc

    caregiver_role = fields.Char(string="Vai trò người chăm sóc")

    created_at = fields.Datetime(string="Ngày tạo", default=fields.Datetime.now)
    updated_at = fields.Datetime(string="Ngày cập nhật")

    @api.model
    def create(self, vals):
        vals['updated_at'] = datetime.now()
        return super(PatientCareTracking, self).create(vals)

    def write(self, vals):
        vals['updated_at'] = datetime.now()
        return super(PatientCareTracking, self).write(vals)
