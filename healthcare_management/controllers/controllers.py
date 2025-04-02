# -*- coding: utf-8 -*-
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
                complaint.write({'state': 'resolved', 'resolution_date': fields.Date.today()})
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
    def patient_complaint_action(self, complaint_id, action, **kw):
        complaint = request.env['healthcare.patient.complaint'].sudo().browse(int(complaint_id))

        if not complaint.exists():
            return {'success': False, 'error': 'Không tìm thấy khiếu nại'}

        try:
            if action == 'open':
                complaint.write({'state': 'open'})
            elif action == 'resolve':
                complaint.write({'state': 'resolved', 'resolution_date': fields.Date.today()})
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