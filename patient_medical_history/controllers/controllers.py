from odoo import http
from odoo.http import request
import logging
from datetime import datetime
from odoo.tools import formataddr
import html
import traceback

_logger = logging.getLogger(__name__)


class PatientHistoryController(http.Controller):
    def _send_otp_email(self, patient, email, otp_code):
        """Helper method to send OTP email using different methods if needed"""
        try:
            # Method 1: Using mail.mail model directly (fallback method)
            company = request.env['res.company'].sudo().search([], limit=1)
            company_email = company.email or 'noreply@example.com'

            subject = f"OTP để truy cập lịch sử y tế của bạn"
            body_html = f"""
            <div style="padding:15px; font-family:Arial, Helvetica, sans-serif; font-size:14px;">
                <p>Chào {html.escape(patient.name)},</p>
                <p>Bạn đã yêu cầu xem lịch sử y tế của mình. Để xác minh danh tính của bạn, vui lòng sử dụng mã OTP sau:</p>
                <div style="background-color:#f8f9fa; padding:10px; text-align:center; font-size:24px; font-weight:bold; letter-spacing:5px;">
                    {otp_code}
                </div>
                <p>Mã này sẽ hết hạn trong 10 phút.</p>
                <p>Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này.</p>
                <p>Xin cảm ơn,<br/>Đội ngũ y tế</p>
            </div>
            """

            mail_values = {
                'subject': subject,
                'body_html': body_html,
                'email_from': formataddr((company.name, company_email)),
                'email_to': email,
                'auto_delete': True,
            }

            mail = request.env['mail.mail'].sudo().create(mail_values)
            mail.send()
            return True

        except Exception as e:
            _logger.error(f"Error sending OTP email: {str(e)}")
            _logger.error(traceback.format_exc())
            return False

    @http.route('/clinic/patient_history', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def patient_history(self, **kwargs):
        email = kwargs.get('email', '')
        otp_sent = kwargs.get('otp_sent', False)
        otp_verified = kwargs.get('otp_verified', False)
        otp_error = kwargs.get('otp_error', False)
        patient = False
        history = False

        # Convert string values from URL to boolean
        if isinstance(otp_sent, str):
            otp_sent = otp_sent.lower() == 'true'
        if isinstance(otp_verified, str):
            otp_verified = otp_verified.lower() == 'true'
        if isinstance(otp_error, str):
            otp_error = otp_error.lower() == 'true'

        # Check if form was submitted with email
        if email and request.httprequest.method == 'POST' and not otp_sent:
            # Search for patient by email
            patient = request.env['clinic.patient'].sudo().search([('email', '=', email)], limit=1)

            if patient:
                try:
                    # Generate OTP
                    otp_code = request.env['patient.otp'].sudo().generate_otp(email)

                    # Try to send the OTP email using our helper method
                    if self._send_otp_email(patient, email, otp_code):
                        otp_sent = True
                        _logger.info(f"OTP sent to {email}")
                    else:
                        # If email sending fails, return a user-friendly error
                        _logger.error("Failed to send OTP email")
                        return request.render('patient_medical_history.patient_history_template', {
                            'error': 'Không thể gửi email OTP. Vui lòng thử lại sau hoặc liên hệ với quản trị viên.'
                        })

                except Exception as e:
                    _logger.error(f"Error in OTP process: {str(e)}")
                    _logger.error(traceback.format_exc())
                    return request.render('patient_medical_history.patient_history_template', {
                        'error': 'Đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại sau.'
                    })

        values = {
            'patient': patient,
            'history': history,
            'email': email,
            'otp_sent': otp_sent,
            'otp_verified': otp_verified,
            'otp_error': otp_error
        }
        return request.render('patient_medical_history.patient_history_template', values)

    @http.route('/clinic/verify_otp', type='http', auth='public', website=True, methods=['POST'])
    def verify_otp(self, **kwargs):
        email = kwargs.get('email', '')
        otp_code = kwargs.get('otp_code', '')

        if email and otp_code:
            # Verify OTP
            verified = request.env['patient.otp'].sudo().verify_otp(email, otp_code)

            if verified:
                # Get patient and history data
                patient = request.env['clinic.patient'].sudo().search([('email', '=', email)], limit=1)
                history = False

                if patient:
                    history = request.env['patient.medical.history'].sudo().search([('patient_id', '=', patient.id)],
                                                                                   limit=1)
                    if not history:
                        history = request.env['patient.medical.history'].sudo().create({'patient_id': patient.id})

                values = {
                    'patient': patient,
                    'history': history,
                    'email': email,
                    'otp_sent': True,
                    'otp_verified': True,
                    'otp_error': False
                }
                return request.render('patient_medical_history.patient_history_template', values)
            else:
                # OTP verification failed
                return http.redirect_with_hash(f'/clinic/patient_history?email={email}&otp_sent=true&otp_error=true')

        # Invalid request
        return http.redirect_with_hash('/clinic/patient_history')