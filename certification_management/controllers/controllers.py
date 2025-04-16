# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class CertificationController(http.Controller):
    def _check_manager_access(self):
        """
        Kiểm tra xem người dùng hiện tại có phải là quản lý chứng nhận không
        Trả về True nếu có quyền, False nếu không
        """
        current_user = request.env.user
        is_manager = current_user.has_group('certification_management.group_certification_manager')
        return is_manager

    # Dashboard
    @http.route('/certification/dashboard', type='http', auth='user', website=True)
    def certification_dashboard(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        # Get certification statistics
        Certification = request.env['hospital.certification']

        all_certs = Certification.search_count([])
        valid_certs = Certification.search_count([('state', '=', 'valid')])
        expiring_certs = Certification.search_count([('state', '=', 'expiring')])
        expired_certs = Certification.search_count([('state', '=', 'expired')])

        # Get upcoming inspections
        today = fields.Date.today()
        next_week = today + timedelta(days=7)
        upcoming_inspections = request.env['hospital.inspection'].search([
            ('state', '=', 'planned'),
            ('planned_date', '>=', today),
            ('planned_date', '<=', next_week)
        ], limit=5)

        # Get certificates expiring soon
        expiring_certificates = Certification.search([
            ('state', '=', 'expiring')
        ], limit=5)

        values = {
            'all_certs': all_certs,
            'valid_certs': valid_certs,
            'expiring_certs': expiring_certs,
            'expired_certs': expired_certs,
            'upcoming_inspections': upcoming_inspections,
            'expiring_certificates': expiring_certificates,
        }
        return request.render('certification_management.dashboard_template', values)

    # Certificate routes
    @http.route('/certification/certificates', type='http', auth='user', website=True)
    def certificates(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        # Get certifications with potential filters
        domain = []

        # Handle search
        search_term = kwargs.get('search', '')
        if search_term:
            domain += ['|', '|',
                       ('name', 'ilike', search_term),
                       ('number', 'ilike', search_term),
                       ('authority', 'ilike', search_term)]

        # Handle filters
        filter_state = kwargs.get('state')
        if filter_state:
            domain += [('state', '=', filter_state)]

        filter_type = kwargs.get('certification_type')
        if filter_type:
            domain += [('certification_type', '=', filter_type)]

        certifications = request.env['hospital.certification'].search(domain)

        values = {
            'certifications': certifications,
            'search': search_term,
            'filter_state': filter_state,
            'filter_type': filter_type,
        }
        return request.render('certification_management.certificates_template', values)

    @http.route('/certification/certificate/<model("hospital.certification"):cert_id>', type='http', auth='user',
                website=True)
    def certificate_detail(self, cert_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        values = {
            'certificate': cert_id,
        }
        return request.render('certification_management.certificate_detail_template', values)

    @http.route('/certification/certificate/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def certificate_create(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        if request.httprequest.method == 'POST':
            try:
                # Create new certification
                values = {
                    'name': kwargs.get('name'),
                    'number': kwargs.get('number'),
                    'certification_type': kwargs.get('certification_type'),
                    'authority': kwargs.get('authority'),
                    'issue_date': kwargs.get('issue_date'),
                    'expiry_date': kwargs.get('expiry_date'),
                    'staff_id': int(kwargs.get('staff_id')) if kwargs.get('staff_id') else False,
                    'department_id': int(kwargs.get('department_id')) if kwargs.get('department_id') else False,
                    'description': kwargs.get('description'),
                    'state': 'draft',
                }

                new_cert = request.env['hospital.certification'].create(values)
                return request.redirect('/certification/certificate/%s' % new_cert.id)
            except Exception as e:
                error_message = str(e)
                _logger.error(f"Error creating certificate: {error_message}")

                staff = request.env['clinic.staff'].search([])
                departments = request.env['clinic.department'].search([])

                values = {
                    'error_message': error_message,
                    'staff': staff,
                    'departments': departments,
                    'form_data': kwargs,
                }
                return request.render('certification_management.certificate_form_template', values)
        else:
            # Render the form for GET request
            staff = request.env['clinic.staff'].search([])
            departments = request.env['clinic.department'].search([])

            values = {
                'staff': staff,
                'departments': departments,
                'form_data': {},
            }
            return request.render('certification_management.certificate_form_template', values)

    @http.route('/certification/certificate/<model("hospital.certification"):cert_id>/edit', type='http', auth='user',
                website=True, methods=['GET', 'POST'])
    def certificate_edit(self, cert_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        if request.httprequest.method == 'POST':
            try:
                # Update certification
                values = {
                    'name': kwargs.get('name'),
                    'number': kwargs.get('number'),
                    'certification_type': kwargs.get('certification_type'),
                    'authority': kwargs.get('authority'),
                    'issue_date': kwargs.get('issue_date'),
                    'expiry_date': kwargs.get('expiry_date'),
                    'staff_id': int(kwargs.get('staff_id')) if kwargs.get('staff_id') else False,
                    'department_id': int(kwargs.get('department_id')) if kwargs.get('department_id') else False,
                    'description': kwargs.get('description'),
                }

                cert_id.write(values)
                return request.redirect('/certification/certificate/%s' % cert_id.id)
            except Exception as e:
                error_message = str(e)
                _logger.error(f"Error updating certificate: {error_message}")

                staff = request.env['clinic.staff'].search([])
                departments = request.env['clinic.department'].search([])

                values = {
                    'certificate': cert_id,
                    'error_message': error_message,
                    'staff': staff,
                    'departments': departments,
                }
                return request.render('certification_management.certificate_form_template', values)
        else:
            # Render the form for GET request with existing data
            staff = request.env['clinic.staff'].search([])
            departments = request.env['clinic.department'].search([])

            # Create a dictionary with certificate data
            form_data = {
                'name': cert_id.name,
                'number': cert_id.number,
                'certification_type': cert_id.certification_type,
                'authority': cert_id.authority,
                'issue_date': cert_id.issue_date,
                'expiry_date': cert_id.expiry_date,
                'staff_id': cert_id.staff_id.id if cert_id.staff_id else False,
                'department_id': cert_id.department_id.id if cert_id.department_id else False,
                'description': cert_id.description,
            }

            values = {
                'certificate': cert_id,
                'staff': staff,
                'departments': departments,
                'form_data': form_data,
            }
            return request.render('certification_management.certificate_form_template', values)

    @http.route('/certification/certificate/<model("hospital.certification"):cert_id>/set_valid', type='http',
                auth='user', website=True)
    def certificate_set_valid(self, cert_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        try:
            cert_id.action_set_valid()
        except Exception as e:
            _logger.error(f"Error setting certificate to valid: {str(e)}")
        return request.redirect('/certification/certificate/%s' % cert_id.id)

    @http.route('/certification/certificate/<model("hospital.certification"):cert_id>/renew', type='http', auth='user',
                website=True, methods=['GET', 'POST'])
    def certificate_renew(self, cert_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        if request.httprequest.method == 'POST':
            try:
                # Calculate default new expiry date (1 year from current)
                current_expiry = cert_id.expiry_date
                new_expiry = kwargs.get('new_expiry_date')

                # Create wizard and execute renewal
                wizard = request.env['hospital.certification.renew.wizard'].create({
                    'certification_id': cert_id.id,
                    'new_expiry_date': new_expiry,
                    'notes': kwargs.get('notes', ''),
                })
                wizard.action_confirm_renewal()

                return request.redirect('/certification/certificate/%s' % cert_id.id)
            except Exception as e:
                error_message = str(e)
                _logger.error(f"Error renewing certificate: {error_message}")

                values = {
                    'certificate': cert_id,
                    'error_message': error_message,
                    'form_data': kwargs,
                }
                return request.render('certification_management.certificate_renew_template', values)
        else:
            # Calculate default new expiry date (1 year from current)
            current_expiry = cert_id.expiry_date
            default_new_expiry = current_expiry + timedelta(days=365)

            values = {
                'certificate': cert_id,
                'default_new_expiry': default_new_expiry,
            }
            return request.render('certification_management.certificate_renew_template', values)

    # Inspection routes
    @http.route('/certification/inspections', type='http', auth='user', website=True)
    def inspections(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        # Get inspections with potential filters
        domain = []

        # Handle search
        search_term = kwargs.get('search', '')
        if search_term:
            domain += ['|', '|',
                       ('name', 'ilike', search_term),
                       ('inspector', 'ilike', search_term),
                       ('certification_id.name', 'ilike', search_term)]

        # Handle filters
        filter_state = kwargs.get('state')
        if filter_state:
            domain += [('state', '=', filter_state)]

        filter_result = kwargs.get('result')
        if filter_result:
            domain += [('result', '=', filter_result)]

        inspections = request.env['hospital.inspection'].search(domain)

        values = {
            'inspections': inspections,
            'search': search_term,
            'filter_state': filter_state,
            'filter_result': filter_result,
        }
        return request.render('certification_management.inspections_template', values)

    @http.route('/certification/inspection/<model("hospital.inspection"):insp_id>', type='http', auth='user',
                website=True)
    def inspection_detail(self, insp_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        values = {
            'inspection': insp_id,
        }
        return request.render('certification_management.inspection_detail_template', values)

    @http.route('/certification/inspection/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def inspection_create(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        if request.httprequest.method == 'POST':
            try:
                # Create new inspection
                values = {
                    'name': kwargs.get('name'),
                    'certification_id': int(kwargs.get('certification_id')) if kwargs.get(
                        'certification_id') else False,
                    'planned_date': kwargs.get('planned_date'),
                    'date': kwargs.get('date'),
                    'inspector': kwargs.get('inspector'),
                    'result': kwargs.get('result', 'pending'),
                    'findings': kwargs.get('findings'),
                    'recommendations': kwargs.get('recommendations'),
                    'notes': kwargs.get('notes'),
                    'corrective_action_required': kwargs.get('corrective_action_required') == 'on',
                    'corrective_action': kwargs.get('corrective_action'),
                    'state': 'planned',
                }

                if values.get('date'):
                    values['state'] = 'in_progress'

                new_insp = request.env['hospital.inspection'].create(values)
                return request.redirect('/certification/inspection/%s' % new_insp.id)
            except Exception as e:
                error_message = str(e)
                _logger.error(f"Error creating inspection: {error_message}")

                certifications = request.env['hospital.certification'].search([])

                values = {
                    'error_message': error_message,
                    'certifications': certifications,
                    'form_data': kwargs,
                }
                return request.render('certification_management.inspection_form_template', values)
        else:
            # Render the form for GET request
            certifications = request.env['hospital.certification'].search([])

            # Handle if coming from a specific certificate
            cert_id = kwargs.get('certification_id')
            cert = None
            if cert_id:
                try:
                    cert = request.env['hospital.certification'].browse(int(cert_id))
                except:
                    pass

            values = {
                'certifications': certifications,
                'selected_certification': cert,
                'form_data': {},
            }
            return request.render('certification_management.inspection_form_template', values)

    @http.route('/certification/inspection/<model("hospital.inspection"):insp_id>/edit', type='http', auth='user',
                website=True, methods=['GET', 'POST'])
    def inspection_edit(self, insp_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        if request.httprequest.method == 'POST':
            try:
                # Update inspection
                values = {
                    'name': kwargs.get('name'),
                    'certification_id': int(kwargs.get('certification_id')) if kwargs.get(
                        'certification_id') else False,
                    'planned_date': kwargs.get('planned_date'),
                    'date': kwargs.get('date'),
                    'inspector': kwargs.get('inspector'),
                    'result': kwargs.get('result'),
                    'findings': kwargs.get('findings'),
                    'recommendations': kwargs.get('recommendations'),
                    'notes': kwargs.get('notes'),
                    'corrective_action_required': kwargs.get('corrective_action_required') == 'on',
                    'corrective_action': kwargs.get('corrective_action'),
                }

                insp_id.write(values)
                return request.redirect('/certification/inspection/%s' % insp_id.id)
            except Exception as e:
                error_message = str(e)
                _logger.error(f"Error updating inspection: {error_message}")

                certifications = request.env['hospital.certification'].search([])

                values = {
                    'inspection': insp_id,
                    'error_message': error_message,
                    'certifications': certifications,
                }
                return request.render('certification_management.inspection_form_template', values)
        else:
            # Render the form for GET request with existing data
            certifications = request.env['hospital.certification'].search([])

            values = {
                'inspection': insp_id,
                'certifications': certifications,
                'form_data': insp_id,
            }
            return request.render('certification_management.inspection_form_template', values)

    @http.route('/certification/inspection/<model("hospital.inspection"):insp_id>/start', type='http', auth='user',
                website=True)
    def inspection_start(self, insp_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        try:
            insp_id.action_start()
        except Exception as e:
            _logger.error(f"Error starting inspection: {str(e)}")
        return request.redirect('/certification/inspection/%s' % insp_id.id)

    @http.route('/certification/inspection/<model("hospital.inspection"):insp_id>/complete', type='http', auth='user',
                website=True)
    def inspection_complete(self, insp_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        try:
            insp_id.action_complete()
        except Exception as e:
            _logger.error(f"Error completing inspection: {str(e)}")
        return request.redirect('/certification/inspection/%s' % insp_id.id)

    @http.route('/certification/inspection/<model("hospital.inspection"):insp_id>/cancel', type='http', auth='user',
                website=True)
    def inspection_cancel(self, insp_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        try:
            insp_id.action_cancel()
        except Exception as e:
            _logger.error(f"Error cancelling inspection: {str(e)}")
        return request.redirect('/certification/inspection/%s' % insp_id.id)

    @http.route('/certification/inspection/<model("hospital.inspection"):insp_id>/reset', type='http', auth='user',
                website=True)
    def inspection_reset(self, insp_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        try:
            insp_id.action_reset()
        except Exception as e:
            _logger.error(f"Error resetting inspection: {str(e)}")
        return request.redirect('/certification/inspection/%s' % insp_id.id)

    @http.route('/certification/certificate/<model("hospital.certification"):cert_id>/set_draft', type='http',
                auth='user', website=True)
    def certificate_set_draft(self, cert_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        try:
            cert_id.action_set_draft()
        except Exception as e:
            _logger.error(f"Error setting certificate to draft: {str(e)}")
        return request.redirect('/certification/certificate/%s' % cert_id.id)
