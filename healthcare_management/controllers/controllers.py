# -*- coding: utf-8 -*-
from pydoc import html

from pip._internal.utils import logging

from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta
import json


class HealthcareManagement(http.Controller):
    # Trang chủ
    @http.route('/healthcare/dashboard', type='http', auth='user', website=True)
    def healthcare_dashboard(self, **kw):
        return request.render('healthcare_management.healthcare_dashboard_template', {
            'title': 'Quản lý chăm sóc khách hàng y tế',
        })

    # Phản hồi bệnh nhân
    @http.route('/healthcare/patient_feedback', type='http', auth='user', website=True)
    def patient_feedback_list(self, **kw):
        domain = []

        # Xử lý filter nếu có
        if kw.get('filter_type'):
            domain.append(('feedback_type', '=', kw.get('filter_type')))
        if kw.get('filter_state'):
            domain.append(('state', '=', kw.get('filter_state')))

        feedbacks = request.env['healthcare.patient.feedback'].sudo().search(domain)
        return request.render('healthcare_management.patient_feedback_list_template', {
            'feedbacks': feedbacks,
        })

    @http.route('/healthcare/patient_feedback/<model("healthcare.patient.feedback"):feedback>', type='http',
                auth='user', website=True)
    def patient_feedback_detail(self, feedback, **kw):
        return request.render('healthcare_management.patient_feedback_detail_template', {
            'feedback': feedback,
        })

    @http.route('/healthcare/patient_feedback/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def patient_feedback_create(self, **kw):
        patients = request.env['clinic.patient'].sudo().search([])
        departments = request.env['clinic.department'].sudo().search([])

        if request.httprequest.method == 'POST':
            vals = {
                'patient_id': int(kw.get('patient_id')),
                'department_id': int(kw.get('department_id')) if kw.get('department_id') else False,
                'feedback_type': kw.get('feedback_type'),
                'description': kw.get('description'),
                'satisfaction_rating': kw.get('satisfaction_rating'),
            }
            feedback = request.env['healthcare.patient.feedback'].sudo().create(vals)
            return request.redirect('/healthcare/patient_feedback/%s' % feedback.id)

        return request.render('healthcare_management.patient_feedback_form_template', {
            'patients': patients,
            'departments': departments,
            'feedback_types': [
                ('compliment', 'Khen ngợi'),
                ('suggestion', 'Góp ý'),
                ('complaint', 'Khiếu nại'),
                ('question', 'Hỏi đáp'),
                ('other', 'Khác')
            ],
            'satisfaction_ratings': [
                ('1', 'Rất không hài lòng'),
                ('2', 'Không hài lòng'),
                ('3', 'Bình thường'),
                ('4', 'Hài lòng'),
                ('5', 'Rất hài lòng')
            ],
        })

    # Bảng điều khiển phản hồi
    @http.route('/healthcare/feedback_dashboard', type='http', auth='user', website=True)
    def feedback_dashboard(self, **kw):
        date_from = kw.get('date_from', (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = kw.get('date_to', datetime.today().strftime('%Y-%m-%d'))

        # Sử dụng SQL trực tiếp để lấy thống kê tương tự như model.dashboard
        request.env.cr.execute("""
            SELECT 
                COUNT(*) as total_feedback,
                SUM(CASE WHEN feedback_type = 'compliment' THEN 1 ELSE 0 END) AS total_compliments,
                SUM(CASE WHEN feedback_type = 'complaint' THEN 1 ELSE 0 END) AS total_complaints,
                SUM(CASE WHEN feedback_type = 'suggestion' THEN 1 ELSE 0 END) AS total_suggestions,
                SUM(CASE WHEN feedback_type = 'question' THEN 1 ELSE 0 END) AS total_questions,
                AVG(CASE WHEN satisfaction_numeric > 0 THEN satisfaction_numeric ELSE NULL END) AS avg_satisfaction
            FROM 
                healthcare_feedback_statistics
            WHERE 
                feedback_date >= %s AND feedback_date <= %s
        """, (date_from, date_to))
        summary_stats = request.env.cr.dictfetchone()

        # Thống kê theo phòng ban
        request.env.cr.execute("""
            SELECT 
                d.id AS department_id,
                d.name AS department_name,
                COUNT(fs.id) AS total_feedback,
                SUM(CASE WHEN fs.feedback_type = 'compliment' THEN 1 ELSE 0 END) AS compliments,
                SUM(CASE WHEN fs.feedback_type = 'complaint' THEN 1 ELSE 0 END) AS complaints,
                SUM(CASE WHEN fs.feedback_type = 'suggestion' THEN 1 ELSE 0 END) AS suggestions,
                SUM(CASE WHEN fs.feedback_type = 'question' THEN 1 ELSE 0 END) AS questions,
                SUM(CASE WHEN fs.feedback_type NOT IN ('compliment', 'complaint', 'suggestion', 'question') 
                        OR fs.feedback_type IS NULL THEN 1 ELSE 0 END) AS others,
                AVG(CASE WHEN fs.satisfaction_numeric > 0 THEN fs.satisfaction_numeric ELSE NULL END) AS avg_satisfaction
            FROM 
                healthcare_feedback_statistics fs
            JOIN 
                clinic_department d ON fs.department_id = d.id
            WHERE 
                fs.feedback_date >= %s AND fs.feedback_date <= %s
            GROUP BY 
                d.id, d.name
            ORDER BY 
                d.name
        """, (date_from, date_to))
        department_stats = request.env.cr.dictfetchall()

        # Dữ liệu cho biểu đồ - Có thể được xử lý thêm ở frontend với JS
        request.env.cr.execute("""
            SELECT 
                feedback_type, 
                COUNT(*) as count 
            FROM 
                healthcare_feedback_statistics 
            WHERE 
                feedback_date >= %s AND feedback_date <= %s 
            GROUP BY 
                feedback_type
        """, (date_from, date_to))
        feedback_by_type = request.env.cr.dictfetchall()

        return request.render('healthcare_management.feedback_dashboard_template', {
            'date_from': date_from,
            'date_to': date_to,
            'summary_stats': summary_stats,
            'department_stats': department_stats,
            'feedback_by_type': feedback_by_type,
        })

    # Khiếu nại bệnh nhân
    @http.route('/healthcare/patient_complaint', type='http', auth='user', website=True)
    def patient_complaint_list(self, **kw):
        complaints = request.env['healthcare.patient.complaint'].sudo().search([])
        return request.render('healthcare_management.patient_complaint_list_template', {
            'complaints': complaints,
        })

    @http.route('/healthcare/patient_complaint/<model("healthcare.patient.complaint"):complaint>', type='http',
                auth='user', website=True)
    def patient_complaint_detail(self, complaint, **kw):
        return request.render('healthcare_management.patient_complaint_detail_template', {
            'complaint': complaint,
        })

    # Thống kê phản hồi
    @http.route('/healthcare/feedback_statistics', type='http', auth='user', website=True)
    def feedback_statistics(self, **kw):
        date_from = kw.get('date_from', (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = kw.get('date_to', datetime.today().strftime('%Y-%m-%d'))

        domain = [
            ('feedback_date', '>=', date_from),
            ('feedback_date', '<=', date_to)
        ]

        statistics = request.env['healthcare.feedback.statistics'].sudo().search(domain)

        # Thống kê theo loại phản hồi
        request.env.cr.execute("""
            SELECT 
                feedback_type, 
                COUNT(*) as count 
            FROM 
                healthcare_feedback_statistics 
            WHERE 
                feedback_date >= %s AND feedback_date <= %s 
            GROUP BY 
                feedback_type
        """, (date_from, date_to))
        feedback_by_type = request.env.cr.dictfetchall()

        # Thống kê theo đánh giá
        request.env.cr.execute("""
            SELECT 
                satisfaction_rating, 
                COUNT(*) as count 
            FROM 
                healthcare_feedback_statistics 
            WHERE 
                feedback_date >= %s AND feedback_date <= %s AND
                satisfaction_rating IS NOT NULL
            GROUP BY 
                satisfaction_rating
        """, (date_from, date_to))
        feedback_by_rating = request.env.cr.dictfetchall()

        return request.render('healthcare_management.feedback_statistics_template', {
            'date_from': date_from,
            'date_to': date_to,
            'statistics': statistics,
            'feedback_by_type': feedback_by_type,
            'feedback_by_rating': feedback_by_rating,
        })

    # API cho xử lý thao tác phản hồi (AJAX)
    @http.route('/healthcare/patient_feedback/action', type='json', auth='user', website=True)
    def patient_feedback_action(self, feedback_id, action, **kw):
        feedback = request.env['healthcare.patient.feedback'].sudo().browse(int(feedback_id))

        if not feedback.exists():
            return {'success': False, 'error': 'Không tìm thấy phản hồi'}

        try:
            if action == 'note':
                feedback.action_note()
            elif action == 'cancel':
                feedback.action_cancel()
            elif action == 'new':
                feedback.action_new()
            else:
                return {'success': False, 'error': 'Hành động không hợp lệ'}

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # API cho xử lý thao tác khiếu nại (AJAX)
    @http.route('/healthcare/patient_complaint/action', type='json', auth='user', website=True)
    def patient_complaint_action(self, complaint_id, action, **kw):
        complaint = request.env['healthcare.patient.complaint'].sudo().browse(int(complaint_id))

        if not complaint.exists():
            return {'success': False, 'error': 'Không tìm thấy khiếu nại'}

        try:
            if action == 'open':
                complaint.write({'state': 'open'})
            elif action == 'resolve':
                complaint.write({'state': 'resolved', 'resolved_date': fields.Date.today()})
            elif action == 'cancel':
                complaint.write({'state': 'cancelled'})
            else:
                return {'success': False, 'error': 'Hành động không hợp lệ'}

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # Tạo khiếu nại từ phản hồi bệnh nhân
    @http.route('/healthcare/patient_complaint/create_from_feedback', type='json', auth='user', website=True)
    def create_complaint_from_feedback(self, **kw):
        feedback_id = kw.get('feedback_id')

        if not feedback_id:
            return {'success': False, 'error': 'Thiếu thông tin phản hồi'}

        feedback = request.env['healthcare.patient.feedback'].sudo().browse(int(feedback_id))

        if not feedback.exists():
            return {'success': False, 'error': 'Không tìm thấy phản hồi'}

        try:
            result = feedback.action_create_complaint()
            complaint_id = result.get('res_id')

            if complaint_id:
                return {'success': True, 'complaint_id': complaint_id}
            else:
                return {'success': False, 'error': 'Không thể tạo khiếu nại'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # API cho xử lý thao tác phản hồi (AJAX)
    @http.route('/healthcare/patient_feedback/action', type='json', auth='user', website=True)
    def patient_feedback_action(self, feedback_id, action, **kw):
        feedback = request.env['healthcare.patient.feedback'].sudo().browse(int(feedback_id))

        if not feedback.exists():
            return {'success': False, 'error': 'Không tìm thấy phản hồi'}

        try:
            if action == 'note':
                feedback.action_note()
            elif action == 'cancel':
                feedback.action_cancel()
            elif action == 'new':
                feedback.action_new()
            else:
                return {'success': False, 'error': 'Hành động không hợp lệ'}

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # API cho xử lý thao tác khiếu nại (AJAX)
    @http.route('/healthcare/patient_complaint/action', type='json', auth='user', website=True)
    def patient_complaint_action(self, **kw):
        _logger = logging.getLogger(__name__)
        _logger.info("Complaint action received: %s", kw)

        # For JSON-RPC, parameters come directly from kw
        complaint_id = kw.get('complaint_id')
        action = kw.get('action')

        if not complaint_id or not action:
            _logger.error("Missing parameters: complaint_id=%s, action=%s", complaint_id, action)
            return {'success': False, 'error': 'Thiếu thông tin cần thiết'}

        try:
            _logger.info("Processing complaint ID: %s with action: %s", complaint_id, action)
            complaint = request.env['healthcare.patient.complaint'].sudo().browse(int(complaint_id))

            if not complaint.exists():
                _logger.error("Complaint not found with ID: %s", complaint_id)
                return {'success': False, 'error': 'Không tìm thấy khiếu nại'}

            if action == 'open':
                complaint.action_progress()  # Use the model method for state changes
                _logger.info("Complaint %s marked as in_progress", complaint_id)
            elif action == 'resolve':
                complaint.action_resolve()  # Use the model method
                _logger.info("Complaint %s marked as resolved", complaint_id)
            elif action == 'cancel':
                complaint.action_cancel()  # Use the model method
                _logger.info("Complaint %s marked as cancelled", complaint_id)
            else:
                _logger.error("Invalid action: %s", action)
                return {'success': False, 'error': 'Hành động không hợp lệ'}

            return {'success': True}
        except Exception as e:
            _logger.exception("Error processing complaint action: %s", str(e))
            return {'success': False, 'error': str(e)}

    # Tạo khiếu nại từ phản hồi bệnh nhân
    @http.route('/healthcare/patient_complaint/create_from_feedback', type='json', auth='user', website=True)
    def create_complaint_from_feedback(self, **kw):
        feedback_id = kw.get('feedback_id')

        if not feedback_id:
            return {'success': False, 'error': 'Thiếu thông tin phản hồi'}

        feedback = request.env['healthcare.patient.feedback'].sudo().browse(int(feedback_id))

        if not feedback.exists():
            return {'success': False, 'error': 'Không tìm thấy phản hồi'}

        try:
            result = feedback.action_create_complaint()
            complaint_id = result.get('res_id')

            if complaint_id:
                return {'success': True, 'complaint_id': complaint_id}
            else:
                return {'success': False, 'error': 'Không thể tạo khiếu nại'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # Complaint Dashboard
    @http.route('/healthcare/complaint_dashboard', type='http', auth='user', website=True)
    def complaint_dashboard(self, **kw):
        date_from = kw.get('date_from', (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = kw.get('date_to', datetime.today().strftime('%Y-%m-%d'))

        # Sử dụng SQL trực tiếp để lấy thống kê tương tự như model.dashboard
        request.env.cr.execute("""
            SELECT 
                COUNT(*) as total_complaints,
                SUM(CASE WHEN state = 'new' THEN 1 ELSE 0 END) AS new_complaints,
                SUM(CASE WHEN state = 'in_progress' THEN 1 ELSE 0 END) AS in_progress_complaints,
                SUM(CASE WHEN state = 'resolved' THEN 1 ELSE 0 END) AS resolved_complaints,
                SUM(CASE WHEN state = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_complaints,
                AVG(CASE WHEN resolution_time > 0 THEN resolution_time ELSE NULL END) AS avg_resolution_time
            FROM 
                healthcare_complaint_statistics
            WHERE 
                complaint_date >= %s AND complaint_date <= %s
        """, (date_from, date_to))
        summary_stats = request.env.cr.dictfetchone()

        # Thống kê theo phân loại
        request.env.cr.execute("""
            SELECT 
                c.id AS category_id,
                c.category AS category,
                CASE
                    WHEN c.category = 'service' THEN 'Dịch vụ'
                    WHEN c.category = 'staff' THEN 'Nhân viên'
                    WHEN c.category = 'facility' THEN 'Cơ sở vật chất'
                    WHEN c.category = 'billing' THEN 'Thanh toán'
                    ELSE 'Khác'
                END AS category_name,
                COUNT(c.id) AS total_complaints,
                SUM(CASE WHEN c.state = 'new' THEN 1 ELSE 0 END) AS new_count,
                SUM(CASE WHEN c.state = 'in_progress' THEN 1 ELSE 0 END) AS in_progress_count,
                SUM(CASE WHEN c.state = 'resolved' THEN 1 ELSE 0 END) AS resolved_count,
                SUM(CASE WHEN c.state = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_count,
                AVG(CASE WHEN c.resolution_time > 0 THEN c.resolution_time ELSE NULL END) AS avg_resolution_time
            FROM 
                healthcare_complaint_statistics c
            WHERE 
                c.complaint_date >= %s AND c.complaint_date <= %s
            GROUP BY 
                c.id, c.category
            ORDER BY 
                c.category
        """, (date_from, date_to))
        category_stats = request.env.cr.dictfetchall()

        # Dữ liệu cho biểu đồ - Khiếu nại theo phân loại
        request.env.cr.execute("""
            SELECT 
                category, 
                COUNT(*) as count 
            FROM 
                healthcare_complaint_statistics 
            WHERE 
                complaint_date >= %s AND complaint_date <= %s 
            GROUP BY 
                category
        """, (date_from, date_to))
        complaint_by_category = request.env.cr.dictfetchall()

        # Dữ liệu cho biểu đồ - Khiếu nại theo tháng
        request.env.cr.execute("""
            SELECT 
                TO_CHAR(complaint_date, 'YYYY-MM') as month_key,
                TO_CHAR(complaint_date, 'MM/YYYY') as month_name,
                state,
                COUNT(*) as count
            FROM 
                healthcare_complaint_statistics 
            WHERE 
                complaint_date >= %s AND complaint_date <= %s 
            GROUP BY 
                month_key, month_name, state
            ORDER BY
                month_key
        """, (date_from, date_to))
        monthly_data = request.env.cr.dictfetchall()

        # Chuyển đổi dữ liệu theo tháng để phù hợp với format biểu đồ
        complaint_by_month = []
        months = {}

        for data in monthly_data:
            month_key = data['month_key']
            if month_key not in months:
                months[month_key] = {
                    'month_name': data['month_name'],
                    'new': 0,
                    'in_progress': 0,
                    'resolved': 0,
                    'cancelled': 0
                }

            state = data['state']
            if state:
                months[month_key][state] = data['count']

        for month_key, data in months.items():
            complaint_by_month.append(data)

        return request.render('healthcare_management.complaint_dashboard_template', {
            'date_from': date_from,
            'date_to': date_to,
            'summary_stats': summary_stats,
            'category_stats': category_stats,
            'complaint_by_category': json.dumps(complaint_by_category),
            'complaint_by_month': json.dumps(complaint_by_month),
        })

    # Complaint Statistics
    @http.route('/healthcare/complaint_statistics', type='http', auth='user', website=True)
    def complaint_statistics(self, **kw):
        date_from = kw.get('date_from', (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = kw.get('date_to', datetime.today().strftime('%Y-%m-%d'))
        filter_category = kw.get('filter_category', False)

        domain = [
            ('complaint_date', '>=', date_from),
            ('complaint_date', '<=', date_to)
        ]

        if filter_category:
            domain.append(('category', '=', filter_category))

        statistics = request.env['healthcare.complaint.statistics'].sudo().search(domain)

        # Thống kê theo phân loại
        request.env.cr.execute("""
            SELECT 
                category, 
                COUNT(*) as count 
            FROM 
                healthcare_complaint_statistics 
            WHERE 
                complaint_date >= %s AND complaint_date <= %s 
                """ + ("""AND category = %s""" if filter_category else "") + """
            GROUP BY 
                category
        """, (date_from, date_to) + ((filter_category,) if filter_category else ()))
        category_data = request.env.cr.dictfetchall()

        # Thống kê trung bình thời gian giải quyết theo phân loại
        request.env.cr.execute("""
            SELECT 
                category,
                AVG(resolution_time) as avg_time 
            FROM 
                healthcare_complaint_statistics 
            WHERE 
                complaint_date >= %s AND complaint_date <= %s 
                AND resolution_time > 0
                """ + ("""AND category = %s""" if filter_category else "") + """
            GROUP BY 
                category
        """, (date_from, date_to) + ((filter_category,) if filter_category else ()))
        resolution_data = request.env.cr.dictfetchall()

        # Thống kê theo trạng thái
        request.env.cr.execute("""
            SELECT 
                state,
                COUNT(*) as count 
            FROM 
                healthcare_complaint_statistics 
            WHERE 
                complaint_date >= %s AND complaint_date <= %s 
                """ + ("""AND category = %s""" if filter_category else "") + """
            GROUP BY 
                state
        """, (date_from, date_to) + ((filter_category,) if filter_category else ()))
        state_rows = request.env.cr.dictfetchall()

        state_data = {}
        for row in state_rows:
            state_data[row['state']] = row['count']

        # Thống kê theo mức độ ưu tiên
        request.env.cr.execute("""
            SELECT 
                priority,
                COUNT(*) as count 
            FROM 
                healthcare_complaint_statistics 
            WHERE 
                complaint_date >= %s AND complaint_date <= %s 
                """ + ("""AND category = %s""" if filter_category else "") + """
            GROUP BY 
                priority
        """, (date_from, date_to) + ((filter_category,) if filter_category else ()))
        priority_rows = request.env.cr.dictfetchall()

        priority_data = {}
        for row in priority_rows:
            priority_data[row['priority']] = row['count']

        return request.render('healthcare_management.complaint_statistics_template', {
            'date_from': date_from,
            'date_to': date_to,
            'filter_category': filter_category,
            'statistics': statistics,
            'category_data': category_data,
            'resolution_data': resolution_data,
            'state_data': state_data,
            'priority_data': priority_data
        })

    # Appointment Reminder
    @http.route('/healthcare/appointment_reminder', type='http', auth='user', website=True)
    def appointment_reminder_list(self, **kw):
        domain = []

        # Xử lý filter nếu có
        filter_state = kw.get('filter_state')
        filter_date_from = kw.get('filter_date_from')
        filter_date_to = kw.get('filter_date_to')

        if filter_state:
            domain.append(('state', '=', filter_state))
        if filter_date_from:
            domain.append(('appointment_date', '>=', filter_date_from))
        if filter_date_to:
            domain.append(('appointment_date', '<=', filter_date_to))

        try:
            request.env['appointment.reminder'].sudo().action_sync_all_appointments()
        except Exception as e:
            _logger = logging.getLogger(__name__)
            _logger.error("Lỗi khi đồng bộ lịch hẹn: %s", str(e), exc_info=True)

        reminders = request.env['appointment.reminder'].sudo().search(domain)
        return request.render('healthcare_management.appointment_reminder_list_template', {
            'reminders': reminders,
        })

    @http.route('/healthcare/appointment_reminder/<model("appointment.reminder"):reminder>', type='http', auth='user',
                website=True)
    def appointment_reminder_detail(self, reminder, **kw):
        company_name = request.env.user.company_id.name
        return request.render('healthcare_management.appointment_reminder_detail_template', {
            'reminder': reminder,
            'company_name': company_name
        })

    @http.route('/healthcare/appointment_reminder/sync', type='json', auth='user', website=True)
    def appointment_reminder_sync(self, **kw):
        try:
            # Gọi hàm đồng bộ lịch hẹn
            result = request.env['appointment.reminder'].sudo().action_sync_all_appointments()

            # Trích xuất số lượng bản ghi đã tạo
            count = 0
            if result and 'params' in result:
                message = result['params'].get('message', '')
                # Extract number from message like 'Đã tạo X thông báo lịch hẹn mới'
                import re
                match = re.search(r'Đã tạo (\d+)', message)
                if match:
                    count = int(match.group(1))

            return {
                'success': True,
                'count': count
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/healthcare/appointment_reminder/action', type='json', auth='user', website=True)
    def appointment_reminder_action(self, **kw):
        _logger = logging.getLogger(__name__)
        reminder_id = kw.get('reminder_id')
        action = kw.get('action')

        if not reminder_id or not action:
            return {'success': False, 'error': 'Thiếu thông tin cần thiết'}

        try:
            reminder = request.env['appointment.reminder'].sudo().browse(int(reminder_id))
            if not reminder.exists():
                return {'success': False, 'error': 'Không tìm thấy thông báo lịch hẹn'}

            if action == 'send_now':
                # Send email directly using the same approach as medical history
                if not reminder.patient_id.email:
                    return {'success': False, 'error': 'Bệnh nhân không có địa chỉ email'}

                try:
                    # Setup email details
                    company = request.env['res.company'].sudo().search([], limit=1)
                    company_email = company.email or 'noreply@example.com'

                    # Format appointment date
                    appointment_date = reminder.appointment_date
                    formatted_date = appointment_date.strftime("%d/%m/%Y %H:%M:%S")
                    try:
                        user_tz = request.env.user.tz
                        if user_tz:
                            from pytz import timezone
                            user_timezone = timezone(user_tz)
                            appointment_date_tz = appointment_date.astimezone(user_timezone)
                            formatted_date = appointment_date_tz.strftime("%d/%m/%Y %H:%M:%S")
                    except Exception as e:
                        _logger.warning(f"Error formatting date with timezone: {str(e)}")

                    # Create email content
                    subject = "Nhắc nhở: Lịch hẹn khám"
                    body_html = f"""
                    <div style="margin: 0px; padding: 0px; font-size: 13px;">
                        <p style="margin: 0px; padding: 0px; font-size: 13px;">
                            Kính gửi {html.escape(reminder.patient_id.name or 'Quý khách')},
                        </p>
                        <p style="margin: 0px; padding: 0px; font-size: 13px;">
                            Chúng tôi xin gửi lời nhắc nhở về lịch hẹn khám sắp tới của bạn:
                        </p>
                        <ul>
                            <li>Mã lịch hẹn: <strong>{html.escape(reminder.name or '')}</strong></li>
                            <li>Thời gian: <strong>{formatted_date}</strong></li>
                            <li>Bác sĩ: <strong>{html.escape(reminder.staff_id.staff_name or 'Chưa xác định')}</strong></li>
                            <li>Phòng khám: <strong>{html.escape(reminder.room_id.name or 'Chưa xác định')}</strong></li>
                        </ul>
                        <p style="margin: 0px; padding: 0px; font-size: 13px;">
                            Vui lòng đến trước 15 phút để hoàn tất thủ tục.
                        </p>
                        <p style="margin: 0px; padding: 0px; font-size: 13px;">
                            Nếu bạn cần thay đổi lịch hẹn, vui lòng liên hệ với chúng tôi trước ít nhất 24 giờ.
                        </p>
                        <p style="margin: 0px; padding: 0px; font-size: 13px;">
                            Trân trọng,<br/>
                            Phòng khám {html.escape(company.name or '')}
                        </p>
                    </div>
                    """

                    # Setup mail values
                    mail_values = {
                        'subject': subject,
                        'body_html': body_html,
                        'email_to': reminder.patient_id.email,
                        'auto_delete': False,
                    }

                    # Create and send mail directly
                    mail = request.env['mail.mail'].sudo().create(mail_values)
                    _logger.info(f"Created mail.mail record with ID: {mail.id} for reminder {reminder.id}")

                    mail.send(raise_exception=False)
                    _logger.info(f"Mail send attempted for ID: {mail.id}")

                    # Check mail state
                    #mail.refresh()
                    _logger.info(f"Mail state after sending: {mail.state}")

                    # Update reminder status
                    if mail.state in ['sent', 'outgoing']:
                        reminder.write({
                            'state': 'sent',
                            'email_status': 'Email đã được gửi thành công'
                        })
                        return {'success': True}
                    else:
                        reminder.write({
                            'state': 'failed',
                            'email_status': f'Lỗi khi gửi email: Trạng thái email {mail.state}'
                        })
                        return {'success': False, 'error': f'Không thể gửi email. Trạng thái: {mail.state}'}

                except Exception as e:
                    _logger.error(f"Error sending appointment reminder email: {str(e)}")
                    reminder.write({
                        'state': 'failed',
                        'email_status': f'Lỗi khi gửi email: {str(e)}'
                    })
                    return {'success': False, 'error': str(e)}

            elif action == 'cancel':
                reminder.write({'state': 'cancelled'})
                return {'success': True}
            else:
                return {'success': False, 'error': 'Hành động không hợp lệ'}

        except Exception as e:
            _logger.error("Lỗi khi xử lý thông báo: %s", str(e), exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/healthcare/patient_complaint/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def patient_complaint_create(self, **kw):
        patients = request.env['clinic.patient'].sudo().search([])

        # Default values
        patient_id = False
        description = False
        feedback_id = False

        # Check if coming from feedback
        if kw.get('feedback_id'):
            feedback = request.env['healthcare.patient.feedback'].sudo().browse(int(kw.get('feedback_id')))
            if feedback.exists():
                patient_id = feedback.patient_id.id
                description = feedback.description
                feedback_id = feedback.id

        if request.httprequest.method == 'POST':
            vals = {
                'patient_id': int(kw.get('patient_id')),
                'category': kw.get('category'),
                'priority': kw.get('priority', '1'),
                'description': kw.get('description'),
            }

            # Set complaint date if provided
            if kw.get('complaint_date'):
                vals['complaint_date'] = kw.get('complaint_date')

            # Set related feedback if provided
            if kw.get('feedback_id'):
                vals['feedback_id'] = int(kw.get('feedback_id'))

            # Create the complaint
            complaint = request.env['healthcare.patient.complaint'].sudo().create(vals)
            return request.redirect('/healthcare/patient_complaint/%s' % complaint.id)

        return request.render('healthcare_management.patient_complaint_form_template', {
            'patients': patients,
            'patient_id': patient_id,
            'description': description,
            'feedback_id': feedback_id,
            'datetime': datetime,
        })