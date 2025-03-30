from odoo import models, fields, api, _
from datetime import datetime


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

    def action_book_appointment(self):
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
            'state': 'confirmed',
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