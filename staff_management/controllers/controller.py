# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from datetime import datetime


class StaffManagementController(http.Controller):

    # === Staff List ===
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
            'active_tab': 'staff',
        }
        return request.render('staff_management.staff_list_template', values)

    # === Staff Type CRUD Operations ===
    @http.route('/clinic/staff_type', type='http', auth='public', website=True)
    def staff_type_list(self, **kwargs):
        """Display list of staff types"""
        staff_types = request.env['clinic.staff.type'].sudo().search([])

        success = kwargs.get('success')
        error = kwargs.get('error')

        values = {
            'staff_types': staff_types,
            'active_tab': 'staff_type',
            'success': success,
            'error': error,
        }
        return request.render('staff_management.staff_type_list_template', values)

    @http.route('/clinic/staff_type/create', type='http', auth='public', website=True)
    def staff_type_create(self, **kwargs):
        """Display form to create a new staff type"""
        values = {
            'staff_type': None,
            'mode': 'create',
            'active_tab': 'staff_type',
        }
        return request.render('staff_management.staff_type_form_template', values)

    @http.route('/clinic/staff_type/<model("clinic.staff.type"):staff_type_id>/edit', type='http', auth='public',
                website=True)
    def staff_type_edit(self, staff_type_id, **kwargs):
        """Display form to edit an existing staff type"""
        values = {
            'staff_type': staff_type_id,
            'mode': 'edit',
            'active_tab': 'staff_type',
        }
        return request.render('staff_management.staff_type_form_template', values)

    @http.route('/clinic/staff_type/save', type='http', auth='public', website=True, methods=['POST'])
    def staff_type_save(self, **kwargs):
        """Save new or updated staff type"""
        mode = kwargs.get('mode', 'create')
        position = kwargs.get('position', '').strip()
        note = kwargs.get('note', '').strip()
        staff_type_id = kwargs.get('staff_type_id')

        if not position:
            return request.redirect('/clinic/staff_type?error=Vui lòng nhập tên chức vụ')

        try:
            if mode == 'create':
                # Create new staff type
                request.env['clinic.staff.type'].sudo().create({
                    'position': position,
                    'note': note,
                })
                success_message = 'Tạo chức vụ mới thành công!'
            else:
                # Update existing staff type
                staff_type = request.env['clinic.staff.type'].sudo().browse(int(staff_type_id))
                staff_type.write({
                    'position': position,
                    'note': note,
                })
                success_message = 'Cập nhật chức vụ thành công!'

            return request.redirect(f'/clinic/staff_type?success={success_message}')
        except Exception as e:
            return request.redirect(f'/clinic/staff_type?error={str(e)}')

    @http.route('/clinic/staff_type/<model("clinic.staff.type"):staff_type_id>/delete', type='http', auth='public',
                website=True)
    def staff_type_delete(self, staff_type_id, **kwargs):
        """Delete a staff type"""
        try:
            # Check if the staff type is being used by any staff
            staff_count = request.env['clinic.staff'].sudo().search_count([('staff_type', '=', staff_type_id.id)])
            if staff_count > 0:
                return request.redirect(
                    f'/clinic/staff_type?error=Không thể xóa chức vụ này vì đang được sử dụng bởi {staff_count} nhân viên')

            position = staff_type_id.position  # Save the name before deletion
            staff_type_id.sudo().unlink()
            return request.redirect(f'/clinic/staff_type?success=Đã xóa chức vụ "{position}" thành công')
        except Exception as e:
            return request.redirect(f'/clinic/staff_type?error={str(e)}')

    # === Department CRUD Operations ===
    @http.route('/clinic/department', type='http', auth='public', website=True)
    def department_list(self, **kwargs):
        """Display list of departments"""
        departments = request.env['clinic.department'].sudo().search([])

        success = kwargs.get('success')
        error = kwargs.get('error')

        values = {
            'departments': departments,
            'active_tab': 'department',
            'success': success,
            'error': error,
        }
        return request.render('staff_management.department_list_template', values)

    @http.route('/clinic/department/create', type='http', auth='public', website=True)
    def department_create(self, **kwargs):
        """Display form to create a new department"""
        values = {
            'department': None,
            'mode': 'create',
            'active_tab': 'department',
        }
        return request.render('staff_management.department_form_template', values)

    @http.route('/clinic/department/<model("clinic.department"):department_id>/edit', type='http', auth='public',
                website=True)
    def department_edit(self, department_id, **kwargs):
        """Display form to edit an existing department"""
        values = {
            'department': department_id,
            'mode': 'edit',
            'active_tab': 'department',
        }
        return request.render('staff_management.department_form_template', values)

    @http.route('/clinic/department/save', type='http', auth='public', website=True, methods=['POST'])
    def department_save(self, **kwargs):
        """Save new or updated department"""
        mode = kwargs.get('mode', 'create')
        department_name = kwargs.get('department_name', '').strip()
        type = kwargs.get('type', '').strip()
        note = kwargs.get('note', '').strip()
        department_id = kwargs.get('department_id')

        if not department_name:
            return request.redirect('/clinic/department?error=Vui lòng nhập tên khoa')

        if not type:
            return request.redirect('/clinic/department?error=Vui lòng chọn loại khoa')

        try:
            if mode == 'create':
                # Create new department
                request.env['clinic.department'].sudo().create({
                    'department_name': department_name,
                    'type': type,
                    'note': note,
                })
                success_message = 'Tạo khoa mới thành công!'
            else:
                # Update existing department
                department = request.env['clinic.department'].sudo().browse(int(department_id))
                department.write({
                    'department_name': department_name,
                    'type': type,
                    'note': note,
                })
                success_message = 'Cập nhật khoa thành công!'

            return request.redirect(f'/clinic/department?success={success_message}')
        except Exception as e:
            return request.redirect(f'/clinic/department?error={str(e)}')

    @http.route('/clinic/department/<model("clinic.department"):department_id>/delete', type='http', auth='public',
                website=True)
    def department_delete(self, department_id, **kwargs):
        """Delete a department"""
        try:
            # Check if the department is being used by any staff
            staff_count = request.env['clinic.staff'].sudo().search_count([('department_id', '=', department_id.id)])
            if staff_count > 0:
                return request.redirect(
                    f'/clinic/department?error=Không thể xóa khoa này vì đang được sử dụng bởi {staff_count} nhân viên')

            department_name = department_id.department_name  # Save the name before deletion
            department_id.sudo().unlink()
            return request.redirect(f'/clinic/department?success=Đã xóa khoa "{department_name}" thành công')
        except Exception as e:
            return request.redirect(f'/clinic/department?error={str(e)}')

    # === Staff CRUD Operations ===
    @http.route('/clinic/staff/create', type='http', auth='public', website=True)
    def staff_create(self, **kwargs):
        """Display form to create a new staff member"""
        staff_types = request.env['clinic.staff.type'].sudo().search([])
        departments = request.env['clinic.department'].sudo().search([])

        values = {
            'staff': None,
            'staff_types': staff_types,
            'departments': departments,
            'mode': 'create',
            'active_tab': 'staff',
        }
        return request.render('staff_management.staff_form_template', values)

    @http.route('/clinic/staff/<model("clinic.staff"):staff_id>/edit', type='http', auth='public', website=True)
    def staff_edit(self, staff_id, **kwargs):
        """Display form to edit an existing staff member"""
        staff_types = request.env['clinic.staff.type'].sudo().search([])
        departments = request.env['clinic.department'].sudo().search([])

        values = {
            'staff': staff_id,
            'staff_types': staff_types,
            'departments': departments,
            'mode': 'edit',
            'active_tab': 'staff',
        }
        return request.render('staff_management.staff_form_template', values)

    @http.route('/clinic/staff/save', type='http', auth='public', website=True, methods=['POST'])
    def staff_save(self, **kwargs):
        """Save new or updated staff member"""
        mode = kwargs.get('mode', 'create')
        staff_id = kwargs.get('staff_id')

        # Collect form data
        values = {
            'staff_name': kwargs.get('staff_name', '').strip(),
            'staff_type': int(kwargs.get('staff_type')) if kwargs.get('staff_type') else False,
            'phone': kwargs.get('phone', '').strip(),
            'email': kwargs.get('email', '').strip(),
            'id_card': kwargs.get('id_card', '').strip(),
            'date_of_birth': kwargs.get('date_of_birth') or False,
            'address': kwargs.get('address', '').strip(),
            'gender': kwargs.get('gender'),
            'department_id': int(kwargs.get('department_id')) if kwargs.get('department_id') else False,
            'license_number': kwargs.get('license_number', '').strip(),
            'qualification': kwargs.get('qualification', '').strip(),
            'experience_year': int(kwargs.get('experience_year', '0')),
            'status': kwargs.get('status', 'active'),
        }

        # Validate required fields
        if not values['staff_name']:
            return request.redirect('/clinic/staff?error=Vui lòng nhập họ và tên')

        if not values['gender']:
            return request.redirect('/clinic/staff?error=Vui lòng chọn giới tính')

        if not values['phone']:
            return request.redirect('/clinic/staff?error=Vui lòng nhập số điện thoại')

        if not values['email']:
            return request.redirect('/clinic/staff?error=Vui lòng nhập địa chỉ email')

        if not values['id_card']:
            return request.redirect('/clinic/staff?error=Vui lòng nhập số CCCD/CMND')

        try:
            if mode == 'create':
                # Create new staff member
                request.env['clinic.staff'].sudo().create(values)
                success_message = 'Tạo nhân viên mới thành công!'
            else:
                # Update existing staff member
                staff = request.env['clinic.staff'].sudo().browse(int(staff_id))
                staff.write(values)
                success_message = 'Cập nhật nhân viên thành công!'

            return request.redirect(f'/clinic/staff?success={success_message}')
        except Exception as e:
            return request.redirect(f'/clinic/staff?error={str(e)}')

    @http.route('/clinic/staff/<model("clinic.staff"):staff_id>/delete', type='http', auth='public', website=True)
    def staff_delete(self, staff_id, **kwargs):
        """Delete a staff member"""
        try:
            # Check if the staff has attendance or performance records
            attendance_count = request.env['clinic.staff.attendance'].sudo().search_count(
                [('staff_id', '=', staff_id.id)])
            performance_count = request.env['clinic.staff.performance'].sudo().search_count(
                [('staff_id', '=', staff_id.id)])

            if attendance_count > 0 or performance_count > 0:
                return request.redirect(
                    f'/clinic/staff?error=Không thể xóa nhân viên này vì có {attendance_count} bản ghi chấm công và {performance_count} đánh giá hiệu suất liên quan')

            staff_name = staff_id.staff_name  # Save the name before deletion
            staff_id.sudo().unlink()
            return request.redirect(f'/clinic/staff?success=Đã xóa nhân viên "{staff_name}" thành công')
        except Exception as e:
            return request.redirect(f'/clinic/staff?error={str(e)}')

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
            'active_tab': 'staff',
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
            'active_tab': 'staff',
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
            'active_tab': 'staff',
        }
        return request.render('staff_management.performance_template', values)