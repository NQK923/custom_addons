from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class StaffType(models.Model):
    _name = 'clinic.staff.type'
    _description = 'Staff Type'

    name = fields.Char(string="Chức vụ", required=True,
                       help="Nhập chức vụ y tế, ví dụ: Bác sĩ Hạng 1, Y tá Hạng 2, v.v.")
    type_code = fields.Char(string="Mã chức vụ", required=True, copy=False, readonly=True,
                            default=lambda self: self.env['ir.sequence'].next_by_code('staff.type.code') or 'ST0001')

    _sql_constraints = [
        ('unique_type_code', 'unique(type_code)', 'Mã chức vụ phải là duy nhất!')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('type_code'):
            vals['type_code'] = self.env['ir.sequence'].next_by_code('staff.type.code') or 'ST0001'
        return super(StaffType, self).create(vals)


class Staff(models.Model):
    _name = 'clinic.staff'
    _description = 'Staff Information'

    staff_code = fields.Char(string="Mã nhân sự", required=True, copy=False, readonly=True,
                             default=lambda self: self.env['ir.sequence'].next_by_code('staff.code') or 'NV0001')
    staff_id = fields.Many2one('res.users', string='Tài khoản người dùng', ondelete='restrict')
    staff_type = fields.Many2one('clinic.staff.type', string='Chức vụ')
    name = fields.Char(string='Họ và Tên', required=True)
    contact_info = fields.Char(string='Thông tin liên lạc')
    date_of_birth = fields.Date(string='Ngày sinh')
    address = fields.Text(string='Địa chỉ')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', required=True)
    faculty = fields.Char(string='Khoa')
    department = fields.Char(string='Phòng')
    license_number = fields.Char(string='Số giấy phép hành nghề', unique=True)
    qualification = fields.Char(string='Trình độ chuyên môn')
    experience_year = fields.Integer(string='Số năm kinh nghiệm')
    status = fields.Selection([
        ('active', 'Đang làm việc'),
        ('inactive', 'Nghỉ phép'),
        ('retired', 'Đã nghỉ hưu')
    ], string='Trạng thái', default='active')
    attendance_ids = fields.One2many('clinic.staff.attendance', 'staff_id', string='Lịch sử chấm công')
    performance_ids = fields.One2many('clinic.staff.performance', 'staff_id', string='Đánh giá hiệu suất')
    labor_type = fields.Selection([
        ('full_time', 'Toàn thời gian'),
        ('part_time', 'Bán thời gian')
    ], string='Loại Lao động', required=True, default='full_time')
    total_salary = fields.Float(string='Tổng lương', compute='_compute_salary_fields', store=False)
    net_salary = fields.Float(string='Thực nhận', compute='_compute_salary_fields', store=False)
    salary_status = fields.Selection([
        ('not_created', 'Chưa lập phiếu'),
        ('created', 'Đã lập phiếu')
    ], string='Trạng thái', compute='_compute_salary_fields', store=False)

    _sql_constraints = [
        ('unique_staff_code', 'unique(staff_code)', 'Mã nhân sự phải là duy nhất!'),
        ('unique_license_number', 'unique(license_number)', 'Số giấy phép hành nghề phải là duy nhất!')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('staff_code'):
            vals['staff_code'] = self.env['ir.sequence'].next_by_code('staff.code') or 'NV0001'
        return super(Staff, self).create(vals)

    # Các hàm khác giữ nguyên...


    def _compute_salary_fields(self):
        for record in self:
            # Lấy bảng lương gần nhất cho nhân viên
            salary_record = self.env['clinic.staff.salary'].search([
                ('staff_id', '=', record.id),
                ('sheet_id', '!=', False)
            ], order='sheet_id.id desc', limit=1)
            if salary_record:
                record.total_salary = salary_record.total_salary
                record.net_salary = salary_record.net_salary
                record.salary_status = 'created'
            else:
                record.total_salary = 0.0
                record.net_salary = 0.0
                record.salary_status = 'not_created'

    def action_create_salary_record(self):
        """Mở form để tạo phiếu lương cho nhân viên"""
        current_month = str(datetime.now().month)
        current_year = str(datetime.now().year)
        salary_record = self.env['clinic.staff.salary'].search([
            ('staff_id', '=', self.id),
            ('month', '=', current_month),
            ('year', '=', current_year)
        ], limit=1)

        if not salary_record:
            return {
                'name': 'Tạo phiếu lương',
                'type': 'ir.actions.act_window',
                'res_model': 'clinic.staff.salary',
                'view_mode': 'form',
                'view_id': self.env.ref('salary_management.view_clinic_staff_salary_form').id,
                'target': 'current',
                'context': {
                    'default_staff_id': self.id,
                    'default_month': current_month,
                    'default_year': current_year,
                },
            }
        else:
            return {
                'warning': {
                    'title': 'Thông báo',
                    'message': 'Phiếu lương cho tháng/năm này đã tồn tại!',
                }
            }

    _sql_constraints = [
        ('unique_license_number', 'unique(license_number)', 'Số giấy phép hành nghề phải là duy nhất!')
    ]

    def action_manual_check_in_out(self):
        today = fields.Date.today()
        for record in self:
            attendance = self.env['clinic.staff.attendance'].search([
                ('staff_id', '=', record.id),
                ('date', '=', today)
            ], limit=1)
            if not attendance:
                self.env['clinic.staff.attendance'].create({
                    'staff_id': record.id,
                    'date': today,
                    'check_in': fields.Datetime.now(),
                })
            elif not attendance.check_out:
                attendance.write({'check_out': fields.Datetime.now()})
            else:
                raise UserError('Nhân viên đã chấm công đầy đủ hôm nay!')

    def action_list_check_in_out(self):
        """Chấm công từ list view"""
        today = fields.Date.today()
        for record in self:
            attendance = self.env['clinic.staff.attendance'].search([
                ('staff_id', '=', record.id),
                ('date', '=', today)
            ], limit=1)
            if not attendance:
                self.env['clinic.staff.attendance'].create({
                    'staff_id': record.id,
                    'date': today,
                    'check_in': fields.Datetime.now(),
                })
            elif not attendance.check_out:
                attendance.write({'check_out': fields.Datetime.now()})
            else:
                raise UserError('Nhân viên %s đã chấm công đầy đủ hôm nay!' % record.name)

    def action_open_performance_form(self):
        """Mở form đánh giá hiệu suất từ form view"""
        for record in self:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'clinic.staff.performance',
                'view_mode': 'form',
                'view_id': self.env.ref('staff_management.view_clinic_staff_performance_form').id,
                'target': 'new',
                'context': {
                    'default_staff_id': record.id,
                    'default_month': str(datetime.now().month),
                    'default_year': str(datetime.now().year),
                },
            }

    def action_list_open_performance_form(self):
        """Mở form đánh giá hiệu suất từ list view"""
        for record in self:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'clinic.staff.performance',
                'view_mode': 'form',
                'view_id': self.env.ref('staff_management.view_clinic_staff_performance_form').id,
                'target': 'new',
                'context': {
                    'default_staff_id': record.id,
                    'default_month': str(datetime.now().month),
                    'default_year': str(datetime.now().year),
                },
            }


class StaffAttendance(models.Model):
    _name = 'clinic.staff.attendance'
    _description = 'Staff Attendance'

    staff_id = fields.Many2one('clinic.staff', string='Mã nhân viên', required=True, ondelete='cascade')
    date = fields.Date(string='Ngày', default=fields.Date.today, required=True)
    check_in = fields.Datetime(string='Giờ vào')
    check_out = fields.Datetime(string='Giờ ra')
    work_hours = fields.Float(string='Số giờ làm việc', compute='_compute_work_hours', store=True)
    status = fields.Selection([
        ('present', 'Có mặt'),
        ('absent', 'Vắng mặt'),
        ('late', 'Đi muộn'),
    ], string='Trạng thái', compute='_compute_status', store=True)

    @api.depends('check_in', 'check_out')
    def _compute_work_hours(self):
        for record in self:
            if record.check_in and record.check_out:
                delta = record.check_out - record.check_in
                record.work_hours = delta.total_seconds() / 3600
            else:
                record.work_hours = 0.0

    @api.depends('check_in')
    def _compute_status(self):
        for record in self:
            if record.check_in:
                start_time = fields.Datetime.from_string(f"{record.date} 08:00:00")
                record.status = 'late' if record.check_in > start_time else 'present'
            else:
                record.status = 'absent'

    _sql_constraints = [
        ('unique_staff_date', 'unique(staff_id, date)', 'Chỉ được chấm công một lần mỗi ngày cho mỗi nhân viên!')
    ]


class StaffPerformance(models.Model):
    _name = 'clinic.staff.performance'
    _description = 'Staff Performance Evaluation'

    staff_id = fields.Many2one('clinic.staff', string='Nhân viên', required=True, ondelete='cascade')
    month = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12')
    ], string='Tháng', required=True, default=str(datetime.now().month))
    year = fields.Selection(
        [(str(year), str(year)) for year in range(2020, 2031)],
        string='Năm', required=True, default=str(datetime.now().year)
    )
    score = fields.Float(string='Điểm đánh giá', compute='_compute_score', store=True)
    attendance_score = fields.Float(string='Điểm chấm công', compute='_compute_attendance_score', store=True)
    work_hours = fields.Float(string='Tổng giờ làm việc', compute='_compute_work_hours', store=True)
    manager_note = fields.Text(string='Ghi chú từ quản lý')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Xác nhận'),
        ('approved', 'Đã duyệt'),
    ], string='Trạng thái', default='draft')

    @api.depends('staff_id', 'month', 'year')
    def _compute_attendance_score(self):
        for record in self:
            if record.staff_id and record.month and record.year:
                month = int(record.month)
                year = int(record.year)
                attendances = record.staff_id.attendance_ids.filtered(
                    lambda a: a.date.month == month and a.date.year == year
                )
                total_days = len(attendances)
                present_days = len(attendances.filtered(lambda a: a.status == 'present'))
                late_days = len(attendances.filtered(lambda a: a.status == 'late'))
                record.attendance_score = (present_days * 1.0) - (late_days * 0.5) if total_days > 0 else 0.0
            else:
                record.attendance_score = 0.0

    @api.depends('staff_id', 'month', 'year')
    def _compute_work_hours(self):
        for record in self:
            if record.staff_id and record.month and record.year:
                month = int(record.month)
                year = int(record.year)
                attendances = record.staff_id.attendance_ids.filtered(
                    lambda a: a.date.month == month and a.date.year == year
                )
                record.work_hours = sum(attendances.mapped('work_hours'))
            else:
                record.work_hours = 0.0

    @api.depends('attendance_score', 'work_hours')
    def _compute_score(self):
        for record in self:
            record.score = record.attendance_score + (record.work_hours * 0.1)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_approve(self):
        self.write({'state': 'approved'})