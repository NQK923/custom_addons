from odoo import http, fields, _
from odoo.http import request
from datetime import datetime, timedelta
import logging
import pytz

_logger = logging.getLogger(__name__)


class AppointmentBookingController(http.Controller):

    @http.route(['/appointment'], type='http', auth="public", website=True)
    def appointment_form(self, **kw):
        doctors = request.env['clinic.staff'].sudo().search([
            ('staff_type.position', 'ilike', 'Bác sĩ'),
            ('status', '=', 'active')
        ])

        exam_rooms = request.env['clinic.room'].sudo().search([
            ('room_type', '=', 'exam')
        ])

        values = {
            'doctors': doctors,
            'exam_rooms': exam_rooms,
            'datetime': datetime,
            'error': kw.get('error'),
        }
        return request.render("clinic_appointment_booking.appointment_booking_form", values)

    def _is_time_valid(self, appointment_time):
        """Check if appointment time is between 8:00 and 21:00"""
        hour = appointment_time.hour
        return 8 <= hour < 21

    def _check_availability(self, doctor_id, room_id, appointment_datetime):
        """
        Kiểm tra xem bác sĩ và phòng khám có rảnh vào thời gian đã chọn không
        Nguyên tắc: Nếu có bất kỳ lịch hẹn nào trong khoảng ±1 giờ, coi như đã bận
        """
        Appointment = request.env['clinic.appointment'].sudo()

        one_hour_before = appointment_datetime - timedelta(hours=1)
        one_hour_after = appointment_datetime + timedelta(hours=1)

        conflicting_doctor_appointments = Appointment.search([
            ('staff_id', '=', doctor_id),
            ('state', 'in', ['draft', 'confirmed']),
            '&',
            ('appointment_date', '>=', one_hour_before),
            ('appointment_date', '<=', one_hour_after)
        ])

        if conflicting_doctor_appointments:
            earliest = min(conflicting_doctor_appointments.mapped('appointment_date'))
            earliest_local = self._convert_utc_to_local(earliest)
            return False, f"Bác sĩ đã có lịch hẹn vào khoảng thời gian này (lúc {earliest_local.strftime('%H:%M')}). Vui lòng chọn thời gian khác."

        if room_id:
            conflicting_room_appointments = Appointment.search([
                ('room_id', '=', room_id),
                ('state', 'in', ['draft', 'confirmed']),
                '&',
                ('appointment_date', '>=', one_hour_before),
                ('appointment_date', '<=', one_hour_after)
            ])

            if conflicting_room_appointments:
                earliest = min(conflicting_room_appointments.mapped('appointment_date'))
                earliest_local = self._convert_utc_to_local(earliest)
                return False, f"Phòng khám đã được sử dụng vào khoảng thời gian này (lúc {earliest_local.strftime('%H:%M')}). Vui lòng chọn phòng khác hoặc đổi thời gian."

        return True, ""

    @http.route(['/appointment/check_availability'], type='json', auth="public", website=True)
    def check_appointment_availability(self, **post):
        """API endpoint to check doctor and room availability"""
        try:
            # Parse date and time
            appointment_date = post.get('appointment_date')
            appointment_time = post.get('appointment_time')
            doctor_id = int(post.get('doctor_id')) if post.get('doctor_id') else False
            room_id = int(post.get('room_id')) if post.get('room_id') else False

            if not appointment_date or not appointment_time or not doctor_id:
                return {'status': 'error', 'message': 'Vui lòng điền đầy đủ thông tin ngày, giờ và bác sĩ.'}

            appointment_datetime_str = f"{appointment_date} {appointment_time}"
            try:
                appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M')
            except ValueError:
                return {'status': 'error', 'message': 'Định dạng thời gian không hợp lệ.'}

            # Check if time is between 8:00 and 21:00
            if not self._is_time_valid(appointment_datetime):
                return {
                    'status': 'error',
                    'message': 'Thời gian hẹn phải từ 8:00 sáng đến 21:00 tối.'
                }

            is_available, message = self._check_availability(doctor_id, room_id, appointment_datetime)

            if not is_available:
                return {'status': 'error', 'message': message}

            return {'status': 'success', 'message': 'Thời gian này có thể đặt lịch hẹn.'}

        except Exception as e:
            _logger.error("Error checking appointment availability: %s", str(e))
            return {'status': 'error', 'message': 'Đã xảy ra lỗi khi kiểm tra. Vui lòng thử lại.'}

    @http.route(['/appointment/submit'], type='http', auth="public", website=True, methods=['POST'])
    def appointment_submit(self, **post):
        # Kiểm tra dữ liệu
        if not post.get('patient_name') or not post.get('phone') or not post.get('appointment_date') or not post.get(
                'appointment_time') or not post.get('doctor_id'):
            return request.redirect('/appointment')

        try:
            appointment_datetime_str = f"{post.get('appointment_date')} {post.get('appointment_time')}"
            try:
                appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M')
            except ValueError:
                appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M:%S')

            if not self._is_time_valid(appointment_datetime):
                return request.redirect('/appointment?error=Thời gian hẹn phải từ 8:00 sáng đến 21:00 tối.')

            doctor_id = int(post.get('doctor_id'))
            room_id = post.get('room_id') and int(post.get('room_id')) or False

            is_available, message = self._check_availability(doctor_id, room_id, appointment_datetime)
            if not is_available:
                return request.redirect(f'/appointment?error={message}')

            Patient = request.env['clinic.patient'].sudo()
            patient = Patient.search([('phone', '=', post.get('phone'))], limit=1)

            if not patient:
                patient_vals = {
                    'name': post.get('patient_name'),
                    'phone': post.get('phone'),
                    'email': post.get('email'),
                    'gender': 'other',
                    'patient_type': 'outpatient',
                    'date': fields.Datetime.now(),
                }
                patient = Patient.create(patient_vals)

            appointment_vals = {
                'patient_id': patient.id,
                'appointment_date': appointment_datetime,
                'staff_id': doctor_id,
                'room_id': room_id,
                'state': 'draft',
                'note': post.get('note'),
            }

            appointment = request.env['clinic.appointment'].sudo().create(appointment_vals)

            doctor = request.env['clinic.staff'].sudo().browse(doctor_id)
            room = room_id and request.env['clinic.room'].sudo().browse(room_id) or False

            values = {
                'appointment_name': appointment.name,
                'appointment_date': appointment.appointment_date,
                'doctor_name': doctor.staff_name,
                'room_name': room and room.name or "Chưa phân phòng"
            }
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
            patient = request.env['clinic.patient'].sudo().search([('phone', '=', post.get('phone'))], limit=1)

            if not patient:
                return request.render("clinic_appointment_booking.appointment_check_results", {
                    'error': 'Không tìm thấy bệnh nhân với số điện thoại này'
                })

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