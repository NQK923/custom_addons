# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from datetime import datetime


class StaffManagementController(http.Controller):

    @http.route('/clinic/staff', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def staff_list(self, **kwargs):
        """Display the list of staff members with search functionality"""
        search_name = kwargs.get('search_name', '')
        search_department = kwargs.get('search_department', '')
        search_status = kwargs.get('search_status', '')

        # Build domain for search
        domain = []
        if search_name:
            domain.append(('staff_name', 'ilike', search_name))
        if search_department:
            domain.append(('department_id.department_name', 'ilike', search_department))
        if search_status:
            domain.append(('status', '=', search_status))

        # Get all staff members
        staff_members = request.env['clinic.staff'].sudo().search(domain)
        departments = request.env['clinic.department'].sudo().search([])

        values = {
            'staff_members': staff_members,
            'departments': departments,
            'search_name': search_name,
            'search_department': search_department,
            'search_status': search_status,
        }
        return request.render('staff_management.staff_list_template', values)

    @http.route('/clinic/staff/<model("clinic.staff"):staff_id>', type='http', auth='public', website=True)
    def staff_detail(self, staff_id, **kwargs):
        """Display detailed information for a specific staff member"""
        # Fetch related attendance records
        attendances = request.env['clinic.staff.attendance'].sudo().search([
            ('staff_id', '=', staff_id.id)
        ], order='date desc', limit=10)

        # Fetch related performance evaluations
        performances = request.env['clinic.staff.performance'].sudo().search([
            ('staff_id', '=', staff_id.id)
        ], order='year desc, month desc', limit=10)

        values = {
            'staff': staff_id,
            'attendances': attendances,
            'performances': performances,
        }
        return request.render('staff_management.staff_detail_template', values)

    @http.route('/clinic/staff/attendance/<model("clinic.staff"):staff_id>', type='http', auth='public', website=True,
                methods=['GET', 'POST'])
    def staff_attendance(self, staff_id, **kwargs):
        """Handle attendance tracking for a staff member"""
        error = None
        success = None

        if request.httprequest.method == 'POST':
            action = kwargs.get('action')
            today = fields.Date.today()

            if action == 'check_in':
                # Check if there's already an attendance record for today
                existing = request.env['clinic.staff.attendance'].sudo().search([
                    ('staff_id', '=', staff_id.id),
                    ('date', '=', today)
                ], limit=1)

                if existing:
                    if existing.check_in and not existing.check_out:
                        error = "Đã chấm công vào ngày hôm nay. Vui lòng chấm công ra."
                    elif existing.check_in and existing.check_out:
                        error = "Đã chấm công đầy đủ cho ngày hôm nay."
                else:
                    # Create new attendance record
                    request.env['clinic.staff.attendance'].sudo().create({
                        'staff_id': staff_id.id,
                        'date': today,
                        'check_in': fields.Datetime.now(),
                    })
                    success = "Chấm công vào thành công!"

            elif action == 'check_out':
                existing = request.env['clinic.staff.attendance'].sudo().search([
                    ('staff_id', '=', staff_id.id),
                    ('date', '=', today)
                ], limit=1)

                if not existing:
                    error = "Chưa có chấm công vào cho ngày hôm nay."
                elif existing.check_out:
                    error = "Đã chấm công ra cho ngày hôm nay."
                else:
                    existing.sudo().write({
                        'check_out': fields.Datetime.now()
                    })
                    success = "Chấm công ra thành công!"

        # Get attendance history
        attendances = request.env['clinic.staff.attendance'].sudo().search([
            ('staff_id', '=', staff_id.id)
        ], order='date desc', limit=30)

        # Check today's attendance status
        today = fields.Date.today()
        today_attendance = request.env['clinic.staff.attendance'].sudo().search([
            ('staff_id', '=', staff_id.id),
            ('date', '=', today)
        ], limit=1)

        values = {
            'staff': staff_id,
            'attendances': attendances,
            'today_attendance': today_attendance,
            'error': error,
            'success': success,
        }
        return request.render('staff_management.attendance_template', values)

    @http.route('/clinic/staff/performance/<model("clinic.staff"):staff_id>', type='http', auth='public', website=True,
                methods=['GET', 'POST'])
    def staff_performance(self, staff_id, **kwargs):
        """Handle performance evaluation for a staff member"""
        error = None
        success = None

        if request.httprequest.method == 'POST':
            # Get form data
            month = kwargs.get('month')
            year = kwargs.get('year')
            manager_note = kwargs.get('manager_note', '')
            action = kwargs.get('action')

            if not month or not year:
                error = "Vui lòng chọn tháng và năm đánh giá."
            else:
                # Check if performance record already exists
                existing = request.env['clinic.staff.performance'].sudo().search([
                    ('staff_id', '=', staff_id.id),
                    ('month', '=', month),
                    ('year', '=', year)
                ], limit=1)

                if not existing and action == 'create':
                    # Create new performance record
                    request.env['clinic.staff.performance'].sudo().create({
                        'staff_id': staff_id.id,
                        'month': month,
                        'year': year,
                        'manager_note': manager_note,
                    })
                    success = "Tạo đánh giá hiệu suất thành công!"

                elif existing and action == 'update':
                    # Update existing record
                    existing.sudo().write({
                        'manager_note': manager_note,
                    })
                    success = "Cập nhật đánh giá hiệu suất thành công!"

                elif existing and action == 'confirm':
                    # Confirm the performance record
                    if existing.state == 'draft':
                        existing.sudo().action_confirm()
                        success = "Xác nhận đánh giá hiệu suất thành công!"
                    else:
                        error = "Không thể xác nhận. Đánh giá đã được xác nhận hoặc duyệt."

                elif existing and action == 'approve':
                    # Approve the performance record
                    if existing.state == 'confirmed':
                        existing.sudo().action_approve()
                        success = "Duyệt đánh giá hiệu suất thành công!"
                    else:
                        error = "Không thể duyệt. Đánh giá chưa được xác nhận hoặc đã được duyệt."

        # Get performance history
        performances = request.env['clinic.staff.performance'].sudo().search([
            ('staff_id', '=', staff_id.id)
        ], order='year desc, month desc')

        # Get current date for default values
        current_month = str(datetime.now().month)
        current_year = str(datetime.now().year)

        values = {
            'staff': staff_id,
            'performances': performances,
            'current_month': current_month,
            'current_year': current_year,
            'years': [str(y) for y in range(2020, 2031)],
            'error': error,
            'success': success,
        }
        return request.render('staff_management.performance_template', values)