from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AppointmentBooking(models.TransientModel):
    _name = 'appointment.booking.wizard'
    _description = 'Đặt lịch hẹn khám'

    name = fields.Char(string='Họ và tên', required=True)
    phone = fields.Char(string='Số điện thoại', required=True)
    email = fields.Char(string='Email')
    appointment_date = fields.Datetime(string='Thời gian hẹn', required=True)
    doctor_id = fields.Many2one(
        'clinic.staff',
        string='Bác sĩ',
        required=True,
        domain=[('staff_type.position', 'ilike', 'Bác sĩ')]
    )
    room_id = fields.Many2one('clinic.room', string='Phòng khám')
    note = fields.Text(string='Ghi chú')

    @api.constrains('appointment_date')
    def _check_appointment_date(self):
        for record in self:
            if record.appointment_date:
                # Require appointments to be at least for tomorrow
                tomorrow = datetime.now() + timedelta(days=1)
                tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

                if record.appointment_date < tomorrow:
                    raise ValidationError(
                        "Không thể đặt lịch hẹn trong quá khứ hoặc hôm nay. Vui lòng chọn ngày mai hoặc sau đó!")

    @api.constrains('doctor_id', 'appointment_date')
    def _check_doctor_availability(self):
        for record in self:
            one_hour_before = record.appointment_date - timedelta(hours=1)
            one_hour_after = record.appointment_date + timedelta(hours=1)

            domain = [
                ('staff_id', '=', record.doctor_id.id),
                ('appointment_date', '>=', one_hour_before),
                ('appointment_date', '<=', one_hour_after),
                ('state', 'not in', ['cancelled']),
            ]

            if self.env['clinic.appointment'].sudo().search_count(domain) > 0:
                raise ValidationError(
                    f"Bác sĩ {record.doctor_id.staff_name} đã có lịch hẹn khác trong vòng 1 tiếng của thời điểm này!")

    @api.constrains('room_id', 'appointment_date')
    def _check_room_availability(self):
        for record in self:
            if record.room_id:
                one_hour_before = record.appointment_date - timedelta(hours=1)
                one_hour_after = record.appointment_date + timedelta(hours=1)

                domain = [
                    ('room_id', '=', record.room_id.id),
                    ('appointment_date', '>=', one_hour_before),
                    ('appointment_date', '<=', one_hour_after),
                    ('state', 'not in', ['cancelled']),
                ]

                if self.env['clinic.appointment'].sudo().search_count(domain) > 0:
                    raise ValidationError(
                        f"Phòng {record.room_id.name} đã được đặt trong vòng 1 tiếng của thời điểm này!")

    def action_book_appointment(self):
        self._check_appointment_date()
        if self.doctor_id:
            self._check_doctor_availability()
        if self.room_id:
            self._check_room_availability()

        # Tìm bệnh nhân theo số điện thoại, nếu không có thì tạo mới
        Patient = self.env['clinic.patient']
        patient = Patient.search([('phone', '=', self.phone)], limit=1)

        if not patient:
            patient_vals = {
                'name': self.name,
                'phone': self.phone,
                'email': self.email,
                'gender': 'other',
                'patient_type': 'outpatient',
                'date': fields.Datetime.now(),
            }
            patient = Patient.create(patient_vals)

        # Tạo lịch hẹn mới
        appointment_vals = {
            'patient_id': patient.id,
            'appointment_date': self.appointment_date,
            'staff_id': self.doctor_id.id,
            'room_id': self.room_id.id if self.room_id else False,
            'state': 'draft',
            'note': self.note,
        }

        appointment = self.env['clinic.appointment'].create(appointment_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Xác nhận đặt lịch hẹn',
            'res_model': 'clinic.appointment',
            'res_id': appointment.id,
            'view_mode': 'form',
            'target': 'new',
        }


class AppointmentCheck(models.TransientModel):
    _name = 'appointment.check.wizard'
    _description = 'Kiểm tra lịch hẹn'

    phone = fields.Char(string='Số điện thoại', required=True)

    def action_check_appointments(self):
        # Tìm bệnh nhân theo số điện thoại
        patient = self.env['clinic.patient'].search([('phone', '=', self.phone)], limit=1)

        if not patient:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thông báo',
                    'message': 'Không tìm thấy bệnh nhân với số điện thoại này',
                    'type': 'warning',
                }
            }

        # Lấy danh sách các lịch hẹn của bệnh nhân
        appointments = self.env['clinic.appointment'].search([
            ('patient_id', '=', patient.id),
            ('appointment_date', '>=', fields.Datetime.now()),
            ('state', 'in', ['draft', 'confirmed'])
        ])

        if not appointments:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thông báo',
                    'message': 'Không có lịch hẹn nào sắp tới',
                    'type': 'warning',
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Danh sách lịch hẹn',
            'res_model': 'clinic.appointment',
            'domain': [('id', 'in', appointments.ids)],
            'view_mode': 'list,form',
            'target': 'new',
        }


class PatientOTP(models.Model):
    _name = 'patient.otp'
    _description = 'Mã OTP xác minh bệnh nhân'
    _rec_name = 'email'

    email = fields.Char(string='Email', required=True, index=True)
    otp_code = fields.Char(string='Mã OTP', required=True)
    expiry_time = fields.Datetime(string='Thời gian hết hạn', required=True)
    is_used = fields.Boolean(string='Đã sử dụng', default=False)

    @api.model
    def generate_otp(self, email):
        """Generate a new OTP for the given email"""
        import random
        import string
        from datetime import datetime, timedelta

        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))

        # Set expiry time to 10 minutes from now
        expiry_time = datetime.now() + timedelta(minutes=10)

        # Delete any existing unused OTPs for this email
        self.search([('email', '=', email), ('is_used', '=', False)]).unlink()

        # Create new OTP record
        self.create({
            'email': email,
            'otp_code': otp_code,
            'expiry_time': expiry_time,
            'is_used': False
        })

        return otp_code

    @api.model
    def verify_otp(self, email, otp_code):
        """Verify if the OTP is valid for the given email"""
        otp_record = self.search([
            ('email', '=', email),
            ('otp_code', '=', otp_code),
            ('is_used', '=', False),
            ('expiry_time', '>=', fields.Datetime.now())
        ], limit=1)

        if otp_record:
            # Mark OTP as used
            otp_record.write({'is_used': True})
            return True
        return False
