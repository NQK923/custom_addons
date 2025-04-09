# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, ValidationError


class ComplianceManagementController(http.Controller):
    # Dashboard chính
    @http.route('/compliance/dashboard', type='http', auth='user', website=True)
    def compliance_dashboard(self, **kw):
        # Lấy các đánh giá tuân thủ gần đây
        recent_compliances = request.env['health.compliance'].sudo().search(
            [], order="date_assessment desc", limit=10)

        # Lấy các đánh giá sắp tới hạn (next_assessment trong vòng 30 ngày)
        today = datetime.now().date()
        due_date = today + timedelta(days=30)
        upcoming_assessments = request.env['health.compliance'].sudo().search([
            ('next_assessment', '>=', today),
            ('next_assessment', '<=', due_date)
        ], order="next_assessment asc")

        # Thống kê trạng thái tuân thủ
        compliance_stats = {
            'compliant': request.env['health.compliance'].sudo().search_count([('state', '=', 'compliant')]),
            'non_compliant': request.env['health.compliance'].sudo().search_count([('state', '=', 'non_compliant')]),
            'partly_compliant': request.env['health.compliance'].sudo().search_count(
                [('state', '=', 'partly_compliant')]),
            'in_progress': request.env['health.compliance'].sudo().search_count([('state', '=', 'in_progress')]),
            'draft': request.env['health.compliance'].sudo().search_count([('state', '=', 'draft')])
        }

        # Thống kê phạm vi quy định
        regulation_stats = {
            'national': request.env['health.regulation'].sudo().search_count([('scope', '=', 'national')]),
            'international': request.env['health.regulation'].sudo().search_count([('scope', '=', 'international')]),
            'local': request.env['health.regulation'].sudo().search_count([('scope', '=', 'local')])
        }

        values = {
            'recent_compliances': recent_compliances,
            'upcoming_assessments': upcoming_assessments,
            'compliance_stats': compliance_stats,
            'regulation_stats': regulation_stats,
            'page_name': 'dashboard'
        }

        return request.render('compliance_management.compliance_dashboard_template', values)

    # Danh sách đánh giá tuân thủ
    @http.route('/compliance/assessments', type='http', auth='user', website=True)
    def compliance_list(self, **kw):
        # Xử lý các tham số tìm kiếm và lọc
        search_term = kw.get('search', '')
        filter_state = kw.get('state', '')

        domain = []
        if search_term:
            domain += ['|', ('name', 'ilike', search_term), ('regulation_id.name', 'ilike', search_term)]
        if filter_state:
            domain += [('state', '=', filter_state)]

        # Lấy danh sách đánh giá tuân thủ
        compliances = request.env['health.compliance'].sudo().search(domain, order="date_assessment desc")

        # Lấy danh sách các phòng ban để hiển thị trong filter
        departments = request.env['clinic.department'].sudo().search([])

        values = {
            'compliances': compliances,
            'departments': departments,
            'search': search_term,
            'filter_state': filter_state,
            'page_name': 'assessments'
        }

        return request.render('compliance_management.compliance_list_template', values)

    # Chi tiết và form đánh giá tuân thủ
    @http.route(['/compliance/assessment/new', '/compliance/assessment/<int:compliance_id>'],
                type='http', auth='user', website=True)
    def compliance_form(self, compliance_id=None, **kw):
        # Mode edit hoặc create
        compliance = None
        if compliance_id:
            compliance = request.env['health.compliance'].sudo().browse(compliance_id)
            if not compliance.exists():
                return request.redirect('/compliance/assessments')

        # Xử lý form submission
        if request.httprequest.method == 'POST':
            # Tạo dict values từ form data
            vals = {
                'name': kw.get('name'),
                'regulation_id': int(kw.get('regulation_id')) if kw.get('regulation_id') else False,
                'department_id': int(kw.get('department_id')) if kw.get('department_id') else False,
                'responsible_id': int(kw.get('responsible_id')) if kw.get('responsible_id') else request.env.user.id,
                'date_assessment': kw.get('date_assessment'),
                'next_assessment': kw.get('next_assessment'),
                'state': kw.get('state'),
                'notes': kw.get('notes')
            }

            try:
                if compliance:
                    # Update
                    compliance.sudo().write(vals)
                else:
                    # Create
                    compliance = request.env['health.compliance'].sudo().create(vals)

                # Chuyển hướng về trang danh sách hoặc trang chi tiết
                return request.redirect(f'/compliance/assessment/{compliance.id}')

            except Exception as e:
                values = {
                    'error_message': str(e),
                    'compliance': compliance,
                    'form_data': kw,
                    'page_name': 'assessment_form'
                }
                return request.render('compliance_management.compliance_form_template', values)

        # Get data cho form
        regulations = request.env['health.regulation'].sudo().search([])
        departments = request.env['clinic.department'].sudo().search([])
        users = request.env['res.users'].sudo().search([])

        values = {
            'compliance': compliance,
            'regulations': regulations,
            'departments': departments,
            'users': users,
            'page_name': 'assessment_form',
            'form_data': {},  # Thêm form_data trống
            'error_message': None
        }

        return request.render('compliance_management.compliance_form_template', values)

    # Danh sách quy định y tế
    @http.route('/compliance/regulations', type='http', auth='user', website=True)
    def regulation_list(self, **kw):
        # Xử lý các tham số tìm kiếm và lọc
        search_term = kw.get('search', '')
        filter_scope = kw.get('scope', '')

        domain = []
        if search_term:
            domain += ['|', '|', ('name', 'ilike', search_term), ('code', 'ilike', search_term),
                       ('authority_id.name', 'ilike', search_term)]
        if filter_scope:
            domain += [('scope', '=', filter_scope)]

        # Lấy danh sách quy định
        regulations = request.env['health.regulation'].sudo().search(domain)

        values = {
            'regulations': regulations,
            'search': search_term,
            'filter_scope': filter_scope,
            'page_name': 'regulations'
        }

        return request.render('compliance_management.regulation_list_template', values)

    # Chi tiết và form quy định y tế
    @http.route(['/compliance/regulation/new', '/compliance/regulation/<int:regulation_id>'],
                type='http', auth='user', website=True)
    def regulation_form(self, regulation_id=None, **kw):
        # Mode edit hoặc create
        regulation = None
        if regulation_id:
            regulation = request.env['health.regulation'].sudo().browse(regulation_id)
            if not regulation.exists():
                return request.redirect('/compliance/regulations')

        # Xử lý form submission
        if request.httprequest.method == 'POST':
            # Tạo dict values từ form data
            vals = {
                'name': kw.get('name'),
                'code': kw.get('code'),
                'authority_id': int(kw.get('authority_id')) if kw.get('authority_id') else False,
                'scope': kw.get('scope'),
                'issue_date': kw.get('issue_date'),
                'effective_date': kw.get('effective_date'),
                'description': kw.get('description')
            }

            try:
                if regulation:
                    # Update
                    regulation.sudo().write(vals)
                else:
                    # Create
                    regulation = request.env['health.regulation'].sudo().create(vals)

                # Chuyển hướng về trang danh sách hoặc trang chi tiết
                return request.redirect(f'/compliance/regulation/{regulation.id}')

            except Exception as e:
                values = {
                    'error_message': str(e),
                    'regulation': regulation,
                    'form_data': kw,
                    'page_name': 'regulation_form'
                }
                return request.render('compliance_management.regulation_form_template', values)

        # Get data cho form
        authorities = request.env['health.authority'].sudo().search([])

        values = {
            'regulation': regulation,
            'authorities': authorities,
            'page_name': 'regulation_form',
            'form_data': {},  # Thêm form_data trống
            'error_message': None
        }

        return request.render('compliance_management.regulation_form_template', values)

    # Danh sách cơ quan quản lý
    @http.route('/compliance/authorities', type='http', auth='user', website=True)
    def authority_list(self, **kw):
        # Xử lý các tham số tìm kiếm
        search_term = kw.get('search', '')

        domain = []
        if search_term:
            domain += ['|', ('name', 'ilike', search_term), ('code', 'ilike', search_term)]

        # Lấy danh sách cơ quan quản lý
        authorities = request.env['health.authority'].sudo().search(domain)

        values = {
            'authorities': authorities,
            'search': search_term,
            'page_name': 'authorities'
        }

        return request.render('compliance_management.authority_list_template', values)

    # Chi tiết và form cơ quan quản lý
    @http.route(['/compliance/authority/new', '/compliance/authority/<int:authority_id>'],
                type='http', auth='user', website=True)
    def authority_form(self, authority_id=None, **kw):
        # Mode edit hoặc create
        authority = None
        if authority_id:
            authority = request.env['health.authority'].sudo().browse(authority_id)
            if not authority.exists():
                return request.redirect('/compliance/authorities')

        # Xử lý form submission
        if request.httprequest.method == 'POST':
            # Tạo dict values từ form data
            vals = {
                'name': kw.get('name'),
                'code': kw.get('code'),
                'country_id': int(kw.get('country_id')) if kw.get('country_id') else False,
                'description': kw.get('description')
            }

            try:
                if authority:
                    # Update
                    authority.sudo().write(vals)
                else:
                    # Create
                    authority = request.env['health.authority'].sudo().create(vals)

                # Chuyển hướng về trang danh sách hoặc trang chi tiết
                return request.redirect(f'/compliance/authority/{authority.id}')

            except Exception as e:
                values = {
                    'error_message': str(e),
                    'authority': authority,
                    'form_data': kw,
                    'page_name': 'authority_form'
                }
                return request.render('compliance_management.authority_form_template', values)

        # Get data cho form
        countries = request.env['res.country'].sudo().search([])

        values = {
            'authority': authority,
            'countries': countries,
            'page_name': 'authority_form',
            'form_data': {},  # Thêm form_data trống
            'error_message': None
        }

        return request.render('compliance_management.authority_form_template', values)
