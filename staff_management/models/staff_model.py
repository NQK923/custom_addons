from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import uuid

class StaffType(models.Model):
    _name = 'clinic.staff.type'
    _description = 'Staff Type'
    _rec_name = 'position' # Tên hiển thị trong list view

    name = fields.Char(string="Mã chức vụ", required=True, copy=False, readonly=True)
    position = fields.Char(string="Chức vụ", required=True,
                          help="Nhập chức vụ y tế, ví dụ: Bác sĩ CKI, Điều dưỡng viên, v.v.")
    note = fields.Text(string="Ghi chú")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default.update(name='New')
        return super().copy(default)

class Department(models.Model):
    _name = 'clinic.department'
    _description = 'Department'
    _rec_name = 'department_name'

    name = fields.Char(string="Mã khoa", required=True, copy=False, readonly=True)
    department_name = fields.Char(string="Tên khoa", required=True,
                                 help="Nhập tên khoa, ví dụ: Khoa Nội, Khoa Xét nghiệm...")
    type = fields.Selection([
        ('clinical', 'Khoa lâm sàng'),
        ('subclinical', 'Khoa cận lâm sàng'),
    ], string="Loại", required=True, help="Phân loại khoa")
    note = fields.Text(string="Ghi chú")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default.update(name='New')
        return super().copy(default)

class Staff(models.Model):
    _name = 'clinic.staff'
    _description = 'Staff Information'
    _rec_name = 'staff_name'

    name = fields.Char(string="Mã nhân sự", required=True, copy=False, readonly=True, default="New")
    staff_name = fields.Char(string='Họ và Tên', required=True)
    staff_type = fields.Many2one('clinic.staff.type', string='Chức vụ')
    contact_info = fields.Char(string='Thông tin liên lạc')
    date_of_birth = fields.Date(string='Ngày sinh')
    address = fields.Text(string='Địa chỉ')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', required=True)
    faculty = fields.Char(string='Khoa')
    department_id = fields.Many2one('clinic.department', string='Khoa')
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

    _sql_constraints = [
        ('unique_license_number', 'unique(license_number)', 'Số giấy phép hành nghề phải là duy nhất!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default.update(name='New')
        return super().copy(default)

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
                raise UserError('Nhân viên %s đã chấm công đầy đủ hôm nay!' % record.staff_name)

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

    staff_id = fields.Many2one('clinic.staff', string='Nhân viên', required=True, ondelete='cascade')
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
                start_time = fields.Datetime.from_string(f"{record.date} 23:00:00")
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