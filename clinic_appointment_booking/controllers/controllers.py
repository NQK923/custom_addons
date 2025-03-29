from odoo import http, fields, _
from odoo.http import request
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class AppointmentBookingController(http.Controller):

    @http.route(['/appointment'], type='http', auth="public", website=True)
    def appointment_form(self, **kw):
        # Lấy danh sách bác sĩ
        doctors = request.env['clinic.staff'].sudo().search([
            ('staff_type.position', 'ilike', 'Bác sĩ'),
            ('status', '=', 'active')
        ])

        values = {
            'doctors': doctors,
            'datetime': datetime,
        }
        return request.render("clinic_appointment_booking.appointment_booking_form", values)

    @http.route(['/appointment/submit'], type='http', auth="public", website=True, methods=['POST'])
    def appointment_submit(self, **post):
        # Kiểm tra dữ liệu
        if not post.get('patient_name') or not post.get('phone') or not post.get('appointment_date') or not post.get(
                'appointment_time') or not post.get('doctor_id'):
            return request.redirect('/appointment')

        try:
            # Chuyển đổi ngày giờ
            appointment_datetime_str = f"{post.get('appointment_date')} {post.get('appointment_time')}"
            appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M:%S')

            # Tìm bệnh nhân theo số điện thoại, nếu không có thì tạo mới
            Patient = request.env['clinic.patient'].sudo()
            patient = Patient.search([('phone', '=', post.get('phone'))], limit=1)

            if not patient:
                patient_vals = {
                    'name': post.get('patient_name'),
                    'phone': post.get('phone'),
                    'email': post.get('email'),
                    'gender': 'other',  # Giá trị mặc định
                    'patient_type': 'outpatient',  # Ngoại trú
                    'date': fields.Datetime.now(),
                }
                patient = Patient.create(patient_vals)

            # Tạo appointment
            appointment_vals = {
                'patient_id': patient.id,
                'appointment_date': appointment_datetime,
                'staff_id': int(post.get('doctor_id')),
                'state': 'draft',
                'note': post.get('note'),
            }

            appointment = request.env['clinic.appointment'].sudo().create(appointment_vals)

            # Chuẩn bị dữ liệu cho trang cảm ơn
            doctor = request.env['clinic.staff'].sudo().browse(int(post.get('doctor_id')))
            values = {
                'appointment_name': appointment.name,
                'appointment_date': appointment.appointment_date,
                'doctor_name': doctor.staff_name
            }

            # Gửi email thông báo nếu có email
            if post.get('email'):
                template = request.env.ref('clinic_appointment_booking.email_template_appointment',
                                        raise_if_not_found=False)
                if template:
                    template.sudo().send_mail(appointment.id, force_send=True)

            return request.render("clinic_appointment_booking.appointment_booking_thankyou", values)

        except Exception as e:
            _logger.error("Error creating appointment: %s", str(e))
            return request.redirect('/appointment')

    @http.route(['/appointment/check'], type='http', auth="public", website=True)
    def appointment_check_form(self, **kw):
        return request.render("clinic_appointment_booking.appointment_check_form")

    @http.route(['/appointment/check/result'], type='http', auth="public", website=True, methods=['POST'])
    def appointment_check_result(self, **post):
        if not post.get('phone'):
            return request.redirect('/appointment/check')

        try:
            # Tìm bệnh nhân theo số điện thoại
            patient = request.env['clinic.patient'].sudo().search([('phone', '=', post.get('phone'))], limit=1)

            if not patient:
                return request.render("clinic_appointment_booking.appointment_check_results", {
                    'error': 'Không tìm thấy bệnh nhân với số điện thoại này'
                })

            # Lấy danh sách các lịch hẹn của bệnh nhân
            appointments = request.env['clinic.appointment'].sudo().search([
                ('patient_id', '=', patient.id),
                ('appointment_date', '>=', fields.Datetime.now()),
                ('state', 'in', ['draft', 'confirmed'])
            ])

            if not appointments:
                return request.render("clinic_appointment_booking.appointment_check_results", {
                    'error': 'Không có lịch hẹn nào sắp tới',
                    'patient': patient
                })

            return request.render("clinic_appointment_booking.appointment_check_results", {
                'appointments': appointments,
                'patient': patient
            })

        except Exception as e:
            _logger.error("Error checking appointments: %s", str(e))
            return request.redirect('/appointment/check')

    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def my_appointments(self, **kw):
        partner = request.env.user.partner_id
        appointments = request.env['clinic.appointment'].sudo().search([
            ('email', '=', partner.email)
        ])

        values = {
            'appointments': appointments
        }
        return request.render("clinic_appointment_booking.portal_my_appointments", values)