# from odoo import http, fields, _
# from odoo.http import request
# from datetime import datetime, timedelta
# import logging
#
# _logger = logging.getLogger(__name__)
#
#
# class AppointmentBookingController(http.Controller):
#
#     @http.route(['/appointment'], type='http', auth="public", website=True)
#     def appointment_form(self, **kw):
#         # Lấy danh sách bác sĩ
#         doctors = request.env['clinic.staff'].sudo().search([
#             ('staff_type.position', '=', 'Bác sĩ'),
#             ('status', '=', 'active')
#         ])
#
#         values = {
#             'doctors': doctors,
#             'datetime': datetime,
#         }
#         return request.render("clinic_appointment_booking.appointment_booking_form", values)
#
#     @http.route(['/appointment/submit'], type='http', auth="public", website=True, methods=['POST'])
#     def appointment_submit(self, **post):
#         # Kiểm tra dữ liệu
#         if not post.get('patient_name') or not post.get('phone') or not post.get('appointment_date') or not post.get(
#                 'appointment_time') or not post.get('doctor_id'):
#             return request.redirect('/appointment')
#
#         try:
#             # Chuyển đổi ngày giờ
#             appointment_datetime_str = f"{post.get('appointment_date')} {post.get('appointment_time')}"
#             appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M:%S')
#
#             # Tạo đối tượng booking
#             vals = {
#                 'patient_name': post.get('patient_name'),
#                 'phone': post.get('phone'),
#                 'email': post.get('email'),
#                 'appointment_date': appointment_datetime,
#                 'doctor_id': int(post.get('doctor_id')),
#                 'note': post.get('note'),
#                 'state': 'draft'
#             }
#
#             # Tạo booking và tự động tạo patient nếu chưa có
#             appointment = request.env['clinic.appointment.booking'].sudo().create(vals)
#
#             # Chuẩn bị dữ liệu cho trang cảm ơn
#             doctor = request.env['clinic.staff'].sudo().browse(int(post.get('doctor_id')))
#             values = {
#                 'appointment_name': appointment.name,
#                 'appointment_date': appointment.appointment_date,
#                 'doctor_name': doctor.staff_name
#             }
#
#             # Gửi email thông báo nếu có email
#             if post.get('email'):
#                 template = request.env.ref('clinic_appointment_booking.email_template_appointment',
#                                            raise_if_not_found=False)
#                 if template:
#                     template.sudo().send_mail(appointment.id, force_send=True)
#
#             return request.render("clinic_appointment_booking.appointment_booking_thankyou", values)
#
#         except Exception as e:
#             _logger.error("Error creating appointment: %s", str(e))
#             return request.redirect('/appointment')
#
#     @http.route(['/my/appointments'], type='http', auth="user", website=True)
#     def my_appointments(self, **kw):
#         partner = request.env.user.partner_id
#         appointments = request.env['clinic.appointment.booking'].sudo().search([
#             ('email', '=', partner.email)
#         ])
#
#         values = {
#             'appointments': appointments
#         }
#         return request.render("clinic_appointment_booking.portal_my_appointments", values)