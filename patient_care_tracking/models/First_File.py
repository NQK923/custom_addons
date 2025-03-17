from odoo import models, fields, api
from datetime import datetime

class PatientCareTracking(models.Model):
    _name = "patient.care.tracking"
    _description = "Theo dõi chăm sóc bệnh nhân"

    patient_id = fields.Many2one(
        'clinic.patient',
        string='Mã bệnh nhân',
        required=True
    )
    care_date = fields.Date(string="Ngày chăm sóc", default=fields.Date.context_today, required=True)
    doctor_id = fields.Many2one('hospital.doctor', string="Nhân viên chăm sóc")

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
