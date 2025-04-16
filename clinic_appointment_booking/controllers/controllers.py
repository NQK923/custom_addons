import html
import logging
import traceback
from datetime import datetime, timedelta

from odoo import http, fields
from odoo.exceptions import ValidationError
from odoo.http import request

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

        # Calculate minimum date for appointment (tomorrow)
        min_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        values = {
            'doctors': doctors,
            'exam_rooms': exam_rooms,
            'datetime': datetime,
            'error': kw.get('error'),
            'min_date': min_date
        }
        return request.render("clinic_appointment_booking.appointment_booking_form", values)

    def _check_availability(self, doctor_id, room_id, appointment_datetime):
        """
        Kiểm tra xem bác sĩ và phòng khám có rảnh vào thời gian đã chọn không
        Nguyên tắc: Nếu có bất kỳ lịch hẹn nào trong khoảng ±1 giờ, coi như đã bận
        """
        Appointment = request.env['clinic.appointment'].sudo()

        # Kiểm tra ngày hẹn phải từ ngày mai trở đi
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

        if appointment_datetime < tomorrow:
            return False, "Không thể đặt lịch hẹn trong quá khứ hoặc hôm nay. Vui lòng chọn ngày mai hoặc sau đó!"

        one_hour_before = appointment_datetime - timedelta(hours=1)
        one_hour_after = appointment_datetime + timedelta(hours=1)

        # Kiểm tra xung đột với lịch của bác sĩ
        conflicting_doctor_appointments = Appointment.search([
            ('staff_id', '=', doctor_id),
            ('state', 'not in', ['cancelled']),
            ('appointment_date', '>=', one_hour_before),
            ('appointment_date', '<=', one_hour_after)
        ])

        if conflicting_doctor_appointments:
            doctor = request.env['clinic.staff'].sudo().browse(doctor_id)
            return False, f"Bác sĩ {doctor.staff_name} đã có lịch hẹn khác trong vòng 1 tiếng của thời điểm này!"

        # Kiểm tra xung đột với phòng khám
        if room_id:
            conflicting_room_appointments = Appointment.search([
                ('room_id', '=', room_id),
                ('state', 'not in', ['cancelled']),
                ('appointment_date', '>=', one_hour_before),
                ('appointment_date', '<=', one_hour_after)
            ])

            if conflicting_room_appointments:
                room = request.env['clinic.room'].sudo().browse(room_id)
                return False, f"Phòng {room.name} đã được đặt trong vòng 1 tiếng của thời điểm này!"

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

            is_available, message = self._check_availability(doctor_id, room_id, appointment_datetime)

            if not is_available:
                return {'status': 'error', 'message': message}

            return {'status': 'success', 'message': 'Thời gian này có thể đặt lịch hẹn.'}

        except Exception as e:
            _logger.error("Error checking appointment availability: %s", str(e))
            return {'status': 'error', 'message': 'Đã xảy ra lỗi khi kiểm tra. Vui lòng thử lại.'}

    @http.route(['/appointment/submit'], type='http', auth="public", website=True, methods=['POST'])
    def appointment_submit(self, **post):
        # Log request data for debugging
        _logger.info("Starting appointment_submit with data: %s", post)

        # Kiểm tra dữ liệu
        if not post.get('patient_name') or not post.get('phone') or not post.get('appointment_date') or not post.get(
                'appointment_time') or not post.get('doctor_id'):
            _logger.warning("Missing required fields in form submission")
            return request.redirect('/appointment?error=Vui lòng điền đầy đủ thông tin bắt buộc')

        try:
            # Step 1: Parse date and time
            _logger.info("Parsing appointment date and time")
            appointment_datetime_str = f"{post.get('appointment_date')} {post.get('appointment_time')}"
            try:
                appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M')
            except ValueError:
                try:
                    appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    _logger.error("Invalid date/time format: %s", appointment_datetime_str)
                    return request.redirect('/appointment?error=Định dạng thời gian không hợp lệ')

            # Step 2: Get doctor and room IDs
            doctor_id = int(post.get('doctor_id'))
            room_id = post.get('room_id') and int(post.get('room_id')) or False

            # Step 3: Check availability
            _logger.info("Checking availability for doctor %s and room %s", doctor_id, room_id)
            is_available, message = self._check_availability(doctor_id, room_id, appointment_datetime)
            if not is_available:
                _logger.warning("Availability check failed: %s", message)
                return request.redirect(f'/appointment?error={message}')

            # Step 4: Find or create patient
            _logger.info("Finding or creating patient with phone: %s", post.get('phone'))
            Patient = request.env['clinic.patient'].sudo()
            patient = Patient.search([('phone', '=', post.get('phone'))], limit=1)

            if not patient:
                _logger.info("Creating new patient record")
                patient_vals = {
                    'name': post.get('patient_name'),
                    'phone': post.get('phone'),
                    'email': post.get('email'),
                    'gender': 'other',
                    'patient_type': 'outpatient',
                    'date': fields.Datetime.now(),
                }
                patient = Patient.create(patient_vals)

            # Step 5: Create appointment
            _logger.info("Creating appointment for patient %s", patient.id)
            appointment_vals = {
                'patient_id': patient.id,
                'appointment_date': appointment_datetime,
                'staff_id': doctor_id,
                'room_id': room_id,
                'state': 'draft',
                'note': post.get('note'),
            }

            appointment = request.env['clinic.appointment'].sudo().create(appointment_vals)
            _logger.info("Appointment created successfully with ID: %s", appointment.id)

            doctor = request.env['clinic.staff'].sudo().browse(doctor_id)
            room = room_id and request.env['clinic.room'].sudo().browse(room_id) or False

            # Step 6: Prepare values for thank you page
            values = {
                'appointment_name': appointment.name,
                'appointment_date': appointment.appointment_date,
                'doctor_name': doctor.staff_name,
                'room_name': room and room.name or "Chưa phân phòng"
            }

            # Step 7: Send email if needed
            if post.get('email'):
                _logger.info("Attempting to send confirmation email")
                template = request.env.ref('clinic_appointment_booking.email_template_appointment',
                                           raise_if_not_found=False)
                if template:
                    _logger.info("Sending confirmation email")
                    template.sudo().send_mail(appointment.id, force_send=True)
                else:
                    _logger.warning("Email template not found")

            # Step 8: Render thank you page
            _logger.info("Rendering thank you page")
            try:
                thank_you_page = request.render("clinic_appointment_booking.appointment_booking_thankyou", values)
                _logger.info("Thank you page rendered successfully")
                return thank_you_page
            except Exception as render_error:
                _logger.error("Error rendering thank you page: %s", str(render_error))
                return request.redirect(
                    '/appointment?error=Lịch hẹn đã được đặt nhưng không thể hiển thị trang xác nhận')

        except ValidationError as ve:
            _logger.error("Validation error creating appointment: %s", str(ve))
            return request.redirect(f'/appointment?error={str(ve)}')
        except Exception as e:
            _logger.error("Error creating appointment: %s", str(e))
            _logger.error(traceback.format_exc())
            return request.redirect(f'/appointment?error=Đã xảy ra lỗi: {str(e)}')

    @http.route(['/appointment/check'], type='http', auth="public", website=True)
    def appointment_check_form(self, **kw):
        email = kw.get('email', '')
        otp_sent = kw.get('otp_sent', False)
        otp_verified = kw.get('otp_verified', False)
        otp_error = kw.get('otp_error', False)
        email_not_found = kw.get('email_not_found', False)
        error = kw.get('error', False)

        # Convert string values from URL to boolean
        if isinstance(otp_sent, str):
            otp_sent = otp_sent.lower() == 'true'
        if isinstance(otp_verified, str):
            otp_verified = otp_verified.lower() == 'true'
        if isinstance(otp_error, str):
            otp_error = otp_error.lower() == 'true'
        if isinstance(email_not_found, str):
            email_not_found = email_not_found.lower() == 'true'

        # Check if form was submitted with email
        if email and request.httprequest.method == 'POST' and not otp_sent:
            # Search for patient by email
            patient = request.env['clinic.patient'].sudo().search([('email', '=', email)], limit=1)

            if patient:
                try:
                    # Generate OTP
                    otp_code = request.env['patient.otp'].sudo().generate_otp(email)

                    # Try to send the OTP email
                    if self._send_otp_email(patient, email, otp_code):
                        otp_sent = True
                        _logger.info(f"OTP sent to {email}")
                    else:
                        # If email sending fails, return a user-friendly error
                        return request.render('clinic_appointment_booking.appointment_check_form', {
                            'error': 'Không thể gửi email OTP. Vui lòng thử lại sau hoặc liên hệ với quản trị viên.'
                        })

                except Exception as e:
                    _logger.error(f"Error in OTP process: {str(e)}")
                    _logger.error(traceback.format_exc())
                    return request.render('clinic_appointment_booking.appointment_check_form', {
                        'error': 'Đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại sau.'
                    })
            else:
                # Email không tồn tại trong hệ thống
                _logger.info(f"Email not found in system: {email}")
                email_not_found = True

        values = {
            'email': email,
            'otp_sent': otp_sent,
            'otp_verified': otp_verified,
            'otp_error': otp_error,
            'email_not_found': email_not_found,
            'error': error
        }
        return request.render("clinic_appointment_booking.appointment_check_form", values)

    def _send_otp_email(self, patient, email, otp_code):
        """Helper method to send OTP email using different methods if needed"""
        try:
            _logger.info(f"Attempting to send OTP email to {email}")

            # Method 1: Using mail.mail model directly
            company = request.env['res.company'].sudo().search([], limit=1)
            company_email = company.email or 'noreply@example.com'

            subject = f"OTP để kiểm tra lịch hẹn khám"
            body_html = f"""
                <div style="padding:15px; font-family:Arial, Helvetica, sans-serif; font-size:14px;">
                    <p>Chào {html.escape(patient.name)},</p>
                    <p>Bạn đã yêu cầu xem lịch hẹn khám của mình. Để xác minh danh tính của bạn, vui lòng sử dụng mã OTP sau:</p>
                    <div style="background-color:#f8f9fa; padding:10px; text-align:center; font-size:24px; font-weight:bold; letter-spacing:5px;">
                        {otp_code}
                    </div>
                    <p>Mã này sẽ hết hạn trong 10 phút.</p>
                    <p>Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này.</p>
                    <p>Xin cảm ơn,<br/>Đội ngũ y tế</p>
                </div>
                """

            # For debugging only - show OTP in logs
            _logger.info(f"OTP code for {email}: {otp_code}")

            # Create mail values
            mail_values = {
                'subject': subject,
                'body_html': body_html,
                'email_to': email,
                'auto_delete': True,
            }

            # Create the mail message
            mail = request.env['mail.mail'].sudo().create(mail_values)
            _logger.info(f"Created mail.mail record with ID: {mail.id}")

            # Try to send the email
            mail.send(raise_exception=False)
            _logger.info(f"Mail send attempted for ID: {mail.id}")

            # Check mail state
            mail.refresh()
            _logger.info(f"Mail state after sending: {mail.state}")

            return True
        except Exception as e:
            _logger.error(f"Error sending OTP email: {str(e)}")
            _logger.error(traceback.format_exc())

            # For development, return True to let the flow continue
            # even if email sending fails
            return True

    @http.route(['/appointment/verify_otp'], type='http', auth="public", website=True, methods=['POST'])
    def verify_appointment_otp(self, **kwargs):
        email = kwargs.get('email', '')
        otp_code = kwargs.get('otp_code', '')

        if email and otp_code:
            # Verify OTP
            verified = request.env['patient.otp'].sudo().verify_otp(email, otp_code)

            if verified:
                # Get patient and appointments data
                patient = request.env['clinic.patient'].sudo().search([('email', '=', email)], limit=1)

                if not patient:
                    return request.redirect('/appointment/check?otp_verified=true')

                appointments = request.env['clinic.appointment'].sudo().search([
                    ('patient_id', '=', patient.id),
                    ('appointment_date', '>=', fields.Datetime.now()),
                    ('state', 'in', ['draft', 'confirmed'])
                ])

                return request.render("clinic_appointment_booking.appointment_check_results", {
                    'patient': patient,
                    'appointments': appointments
                })
            else:
                # OTP verification failed - use standard redirect
                return request.redirect(f'/appointment/check?email={email}&otp_sent=true&otp_error=true')

        # Invalid request
        return request.redirect('/appointment/check')
