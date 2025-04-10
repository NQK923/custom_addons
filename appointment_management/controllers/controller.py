from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta
import json
import pytz
from odoo.exceptions import ValidationError


class AppointmentController(http.Controller):
    @http.route('/clinic/appointments', type='http', auth='user', website=True)
    def appointment_list(self, **kwargs):
        """
        Hiển thị danh sách và lịch hẹn
        """
        # Lấy thông tin bệnh nhân và bác sĩ cho form tạo mới
        patients = request.env['clinic.patient'].sudo().search([])
        doctors = request.env['clinic.staff'].sudo().search([('staff_type', '=', 'Bác sĩ')])
        rooms = request.env['clinic.room'].sudo().search([('room_type', '=', 'exam')])

        # Xử lý filter trạng thái
        state_filter = kwargs.get('state', False)
        domain = []
        if state_filter and state_filter != 'all':
            domain.append(('state', '=', state_filter))
        search_term = kwargs.get('search', '')
        if search_term:
            domain += ['|', '|', '|',
                       ('name', 'ilike', search_term),
                       ('patient_id.name', 'ilike', search_term),
                       ('patient_id.code', 'ilike', search_term),
                       ('staff_id.name', 'ilike', search_term)
                       ]
        date_from = kwargs.get('date_from', False)
        if date_from:
            domain.append(('appointment_date', '>=', date_from + ' 00:00:00'))

        date_to = kwargs.get('date_to', False)
        if date_to:
            domain.append(('appointment_date', '<=', date_to + ' 23:59:59'))

        appointments = request.env['clinic.appointment'].sudo().search(domain, order='appointment_date desc')

        view_mode = kwargs.get('view_mode', 'list')
        calendar_data = []
        if view_mode == 'calendar':
            for app in appointments:
                calendar_data.append({
                    'id': app.id,
                    'title': f"{app.patient_id.name} - {app.staff_id.name}",
                    'start': app.appointment_date.strftime('%Y-%m-%dT%H:%M:%S'),
                    'end': (app.appointment_date + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
                    'url': f'/clinic/appointment/{app.id}',
                    'className': f"appointment-state-{app.state}"
                })

        # Calculate minimum date for appointment (tomorrow)
        min_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        values = {
            'appointments': appointments,
            'patients': patients,
            'doctors': doctors,
            'rooms': rooms,
            'state_filter': state_filter or 'all',
            'view_mode': view_mode,
            'calendar_data': json.dumps(calendar_data),
            'datetime': datetime,
            'search_term': search_term,
            'date_from': date_from,
            'date_to': date_to,
            'min_date': min_date
        }
        return request.render('appointment_management.appointment_list_template', values)

    @http.route('/clinic/appointment/create', type='http', auth='user', website=True, methods=['POST'])
    def appointment_create(self, **post):
        """
        Tạo lịch hẹn mới
        """
        if not post:
            return request.redirect('/clinic/appointments')

        try:
            # Chuyển đổi ngày giờ
            appointment_date_str = post.get('appointment_date', '')
            appointment_time_str = post.get('appointment_time', '')

            if appointment_date_str and appointment_time_str:
                appointment_datetime_str = f"{appointment_date_str} {appointment_time_str}"
                appointment_datetime = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M")

                # Kiểm tra ngày hẹn phải từ ngày mai trở đi
                tomorrow = datetime.now() + timedelta(days=1)
                tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

                if appointment_datetime < tomorrow:
                    raise ValidationError(
                        "Không thể đặt lịch hẹn trong quá khứ hoặc hôm nay. Vui lòng chọn ngày mai hoặc sau đó!")

                # Tạo lịch hẹn mới
                vals = {
                    'patient_id': int(post.get('patient_id')),
                    'staff_id': int(post.get('staff_id')),
                    'appointment_date': appointment_datetime,
                    'note': post.get('note', ''),
                    'state': 'draft'
                }

                # Thêm phòng nếu được chọn
                if post.get('room_id'):
                    vals['room_id'] = int(post.get('room_id'))

                # Kiểm tra xem bác sĩ đã có lịch hẹn vào thời điểm này chưa
                staff_id = int(post.get('staff_id'))
                one_hour_before = appointment_datetime - timedelta(hours=1)
                one_hour_after = appointment_datetime + timedelta(hours=1)

                doctor_conflict = request.env['clinic.appointment'].sudo().search([
                    ('staff_id', '=', staff_id),
                    ('appointment_date', '>=', one_hour_before),
                    ('appointment_date', '<=', one_hour_after),
                    ('state', 'not in', ['cancelled'])
                ])

                if doctor_conflict:
                    doctor = request.env['clinic.staff'].sudo().browse(staff_id)
                    raise ValidationError(
                        f"Bác sĩ {doctor.name} đã có lịch hẹn khác trong vòng 1 tiếng của thời điểm này!")

                # Kiểm tra xem phòng đã được đặt vào thời điểm này chưa
                if post.get('room_id'):
                    room_id = int(post.get('room_id'))
                    room_conflict = request.env['clinic.appointment'].sudo().search([
                        ('room_id', '=', room_id),
                        ('appointment_date', '>=', one_hour_before),
                        ('appointment_date', '<=', one_hour_after),
                        ('state', 'not in', ['cancelled'])
                    ])

                    if room_conflict:
                        room = request.env['clinic.room'].sudo().browse(room_id)
                        raise ValidationError(f"Phòng {room.name} đã được đặt trong vòng 1 tiếng của thời điểm này!")

                # Tạo lịch hẹn
                request.env['clinic.appointment'].sudo().create(vals)

                return request.redirect('/clinic/appointments?success=1')
            else:
                return request.redirect(
                    '/clinic/appointments?error=1&message=Vui lòng điền đầy đủ thông tin ngày giờ hẹn')
        except ValidationError as e:
            return request.redirect(f'/clinic/appointments?error=1&message={e}')
        except Exception as e:
            return request.redirect(f'/clinic/appointments?error=1&message={e}')

    @http.route('/clinic/appointment/<int:appointment_id>', type='http', auth='user', website=True)
    def appointment_detail(self, appointment_id, **kwargs):
        """
        Hiển thị chi tiết lịch hẹn
        """
        appointment = request.env['clinic.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return request.redirect('/clinic/appointments')

        doctors = request.env['clinic.staff'].sudo().search([('staff_type', '=', 'Bác sĩ')])
        rooms = request.env['clinic.room'].sudo().search([('room_type', '=', 'exam')])

        # Calculate minimum date for appointment (tomorrow)
        min_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        values = {
            'appointment': appointment,
            'doctors': doctors,
            'rooms': rooms,
            'datetime': datetime,
            'min_date': min_date
        }

        return request.render('appointment_management.appointment_detail_template', values)

    @http.route('/clinic/appointment/<int:appointment_id>/update', type='http', auth='user', website=True,
                methods=['POST'])
    def appointment_update(self, appointment_id, **post):
        """
        Cập nhật lịch hẹn
        """
        appointment = request.env['clinic.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return request.redirect('/clinic/appointments')

        try:
            # Cập nhật thông tin
            vals = {}

            # Cập nhật bác sĩ nếu thay đổi
            if post.get('staff_id') and int(post.get('staff_id')) != appointment.staff_id.id:
                vals['staff_id'] = int(post.get('staff_id'))

            # Cập nhật phòng nếu thay đổi
            if post.get('room_id') and int(post.get('room_id')) != (appointment.room_id.id or 0):
                vals['room_id'] = int(post.get('room_id'))

            # Cập nhật ngày giờ nếu thay đổi
            if post.get('appointment_date') and post.get('appointment_time'):
                appointment_datetime_str = f"{post.get('appointment_date')} {post.get('appointment_time')}"
                new_datetime = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M")

                # Kiểm tra ngày hẹn phải từ ngày mai trở đi
                tomorrow = datetime.now() + timedelta(days=1)
                tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

                if new_datetime < tomorrow:
                    raise ValidationError(
                        "Không thể cập nhật lịch hẹn vào quá khứ hoặc hôm nay. Vui lòng chọn ngày mai hoặc sau đó!")

                if new_datetime != appointment.appointment_date:
                    vals['appointment_date'] = new_datetime

            # Cập nhật ghi chú
            if post.get('note') != appointment.note:
                vals['note'] = post.get('note', '')

            # Kiểm tra xung đột lịch nếu thay đổi bác sĩ hoặc thời gian
            if ('staff_id' in vals or 'appointment_date' in vals):
                staff_id = vals.get('staff_id', appointment.staff_id.id)
                appointment_date = vals.get('appointment_date', appointment.appointment_date)

                one_hour_before = appointment_date - timedelta(hours=1)
                one_hour_after = appointment_date + timedelta(hours=1)

                doctor_conflict = request.env['clinic.appointment'].sudo().search([
                    ('staff_id', '=', staff_id),
                    ('appointment_date', '>=', one_hour_before),
                    ('appointment_date', '<=', one_hour_after),
                    ('state', 'not in', ['cancelled']),
                    ('id', '!=', appointment_id)
                ])

                if doctor_conflict:
                    doctor = request.env['clinic.staff'].sudo().browse(staff_id)
                    raise ValidationError(
                        f"Bác sĩ {doctor.name} đã có lịch hẹn khác trong vòng 1 tiếng của thời điểm này!")

            # Kiểm tra xung đột phòng nếu thay đổi phòng hoặc thời gian
            if ('room_id' in vals or 'appointment_date' in vals) and (appointment.room_id or 'room_id' in vals):
                room_id = vals.get('room_id', appointment.room_id.id if appointment.room_id else False)
                if room_id:
                    appointment_date = vals.get('appointment_date', appointment.appointment_date)

                    one_hour_before = appointment_date - timedelta(hours=1)
                    one_hour_after = appointment_date + timedelta(hours=1)

                    room_conflict = request.env['clinic.appointment'].sudo().search([
                        ('room_id', '=', room_id),
                        ('appointment_date', '>=', one_hour_before),
                        ('appointment_date', '<=', one_hour_after),
                        ('state', 'not in', ['cancelled']),
                        ('id', '!=', appointment_id)
                    ])

                    if room_conflict:
                        room = request.env['clinic.room'].sudo().browse(room_id)
                        raise ValidationError(f"Phòng {room.name} đã được đặt trong vòng 1 tiếng của thời điểm này!")

            # Lưu thay đổi nếu có
            if vals:
                appointment.write(vals)

            return request.redirect(f'/clinic/appointment/{appointment_id}?updated=1')
        except ValidationError as e:
            return request.redirect(f'/clinic/appointment/{appointment_id}?error=1&message={e}')
        except Exception as e:
            return request.redirect(f'/clinic/appointment/{appointment_id}?error=1&message={e}')

    @http.route('/clinic/appointment/<int:appointment_id>/action', type='http', auth='user', website=True)
    def appointment_action(self, appointment_id, action=None, **kwargs):
        """
        Thực hiện các hành động với lịch hẹn (xác nhận, hoàn thành, hủy, đặt về nháp)
        """
        appointment = request.env['clinic.appointment'].sudo().browse(appointment_id)
        if not appointment.exists() or not action:
            return request.redirect('/clinic/appointments')

        try:
            if action == 'confirm' and appointment.state == 'draft':
                appointment.action_confirm()
            elif action == 'done' and appointment.state == 'confirmed':
                appointment.action_done()
            elif action == 'cancel' and appointment.state in ['draft', 'confirmed']:
                appointment.action_cancel()
            elif action == 'draft' and appointment.state == 'cancelled':
                appointment.action_draft()

            return request.redirect(f'/clinic/appointment/{appointment_id}?action_success=1')
        except Exception as e:
            return request.redirect(f'/clinic/appointment/{appointment_id}?error=1&message={e}')