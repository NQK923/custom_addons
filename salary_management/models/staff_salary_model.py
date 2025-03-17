from odoo import models, fields, api
from datetime import datetime


# Model quản lý hệ số lương (giữ nguyên)
class StaffSalaryQualificationLevel(models.Model):
    _name = 'clinic.staff.salary.qualification_level'
    _description = 'Clinic Staff Salary Qualification Level'

    staff_type_id = fields.Many2one('clinic.staff.type', string='Chức vụ', required=True, ondelete='restrict')
    rank = fields.Selection(
        [(str(i), str(i)) for i in range(1, 16)],  # Từ 1 đến 15
        string='Bậc', required=True
    )
    salary_factor = fields.Float(string='Hệ số lương', required=True, default=1.0,
                                 help='Hệ số nhân với lương cơ sở để tính lương cơ bản')

    _sql_constraints = [
        ('unique_staff_type_rank', 'UNIQUE(staff_type_id, rank)',
         'Một chức vụ và bậc chỉ được gán một hệ số lương duy nhất!'),
    ]


# Model quản lý bảng lương
class SalarySheet(models.Model):
    _name = 'clinic.salary.sheet'
    _description = 'Bảng lương'

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
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã lập'),
    ], string='Trạng thái', default='draft')
    salary_ids = fields.One2many('clinic.staff.salary', 'sheet_id', string='Phiếu lương')

    _sql_constraints = [
        ('unique_month_year', 'UNIQUE(month, year)', 'Bảng lương cho tháng và năm này đã tồn tại!')
    ]

    def action_create_salary_records(self):
        """Tạo phiếu lương cho nhân viên đang làm việc dựa trên bảng lương."""
        staff_model = self.env['clinic.staff']
        # Lấy danh sách nhân viên có status là 'active' (Đang làm việc)
        staffs = staff_model.search([('status', '=', 'active')])
        existing_staff_ids = self.env['clinic.staff.salary'].search([('sheet_id', '=', self.id)]).mapped('staff_id').ids
        staffs_to_create = staffs.filtered(lambda s: s.id not in existing_staff_ids)
        if staffs_to_create:
            salary_records = [{
                'staff_id': staff.id,
                'sheet_id': self.id,
                'state': 'draft'
            } for staff in staffs_to_create]
            self.env['clinic.staff.salary'].create(salary_records)
        # Cập nhật trạng thái bảng lương thành 'confirmed'
        self.write({'state': 'confirmed'})


# Model quản lý phiếu lương
class StaffSalary(models.Model):
    _name = 'clinic.staff.salary'
    _description = 'Clinic Staff Salary'

    sheet_id = fields.Many2one('clinic.salary.sheet', string='Bảng lương', ondelete='cascade', required=True)
    staff_id = fields.Many2one('clinic.staff', string='Nhân viên', required=True, ondelete='cascade')
    allowance_ids = fields.Many2many('clinic.staff.salary.allowance', string='Phụ cấp áp dụng')
    total_allowance = fields.Float(string='Tổng phụ cấp', compute='_compute_total_allowance')
    bonus_ids = fields.Many2many('clinic.staff.salary.bonus', string='Thưởng áp dụng')
    total_bonus = fields.Float(string='Tổng thưởng', compute='_compute_total_bonus')
    deduction_ids = fields.Many2many('clinic.staff.salary.deduction', string='Khấu trừ áp dụng')
    late_penalty = fields.Float(string='Phạt đi trễ', compute='_compute_late_penalty')
    absent_penalty = fields.Float(string='Phạt nghỉ', compute='_compute_absent_penalty')
    total_deduction = fields.Float(string='Tổng khấu trừ', compute='_compute_total_deduction')
    total_salary_after_deduction = fields.Float(string='Tổng lương sau khấu trừ',
                                                compute='_compute_total_salary_after_deduction')
    tax = fields.Float(string='Thuế', compute='_compute_tax')
    work_days = fields.Float(string='Số ngày chấm công', compute='_compute_work_days')
    late_days = fields.Float(string='Số ngày đi trễ', compute='_compute_late_days')
    absent_days = fields.Float(string='Số ngày nghỉ', compute='_compute_absent_days')
    standard_work_days = fields.Float(string='Số ngày công theo quy định', default=26.0, readonly=True)
    base_salary = fields.Float(string='Lương cơ bản', compute='_compute_base_salary', store=True)
    total_salary = fields.Float(string='Tổng lương', compute='_compute_total_salary', store=True)
    net_salary = fields.Float(string='Thực nhận', compute='_compute_net_salary', store=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Xác nhận'),
        ('paid', 'Đã thanh toán'),
    ], string='Trạng thái', default='draft')

    _sql_constraints = [
        ('unique_salary_per_sheet', 'unique(staff_id, sheet_id)',
         'Mỗi nhân viên chỉ có một phiếu lương cho mỗi bảng lương!')
    ]

    BASE_SALARY = 2340000  # 2.340.000 VNĐ

    sheet_name = fields.Char(string='Bảng lương', compute='_compute_sheet_name')

    @api.depends('sheet_id', 'sheet_id.month', 'sheet_id.year')
    def _compute_sheet_name(self):
        for record in self:
            if record.sheet_id:
                month = record.sheet_id.month
                year = record.sheet_id.year
                record.sheet_name = f"Tháng {month}/{year}"
            else:
                record.sheet_name = ''

    @api.depends('staff_id', 'sheet_id')
    def _compute_base_salary(self):
        for record in self:
            if record.staff_id and record.sheet_id:
                staff_type = record.staff_id.staff_type.id
                experience_year = record.staff_id.experience_year or 0
                rank = min(15, (experience_year // 3) + 1)
                qualification_level = self.env['clinic.staff.salary.qualification_level'].search([
                    ('staff_type_id', '=', staff_type),
                    ('rank', '=', str(rank))
                ], limit=1)
                record.base_salary = self.BASE_SALARY * qualification_level.salary_factor if qualification_level else 0.0
            else:
                record.base_salary = 0.0

    @api.depends('allowance_ids')
    def _compute_total_allowance(self):
        for record in self:
            record.total_allowance = sum(record.allowance_ids.mapped('amount')) if record.allowance_ids else 0.0

    @api.depends('bonus_ids')
    def _compute_total_bonus(self):
        for record in self:
            record.total_bonus = sum(record.bonus_ids.mapped('amount')) if record.bonus_ids else 0.0

    @api.depends('base_salary', 'total_allowance', 'total_bonus')
    def _compute_total_salary(self):
        for record in self:
            record.total_salary = (
                        record.base_salary + record.total_allowance + record.total_bonus) if record.base_salary is not None else 0.0

    @api.depends('late_days')
    def _compute_late_penalty(self):
        for record in self:
            record.late_penalty = 50000 * record.late_days if record.late_days else 0.0

    @api.depends('base_salary', 'absent_days', 'standard_work_days')
    def _compute_absent_penalty(self):
        for record in self:
            if record.base_salary and record.standard_work_days:
                daily_salary = record.base_salary / record.standard_work_days
                record.absent_penalty = daily_salary * record.absent_days if record.absent_days else 0.0
            else:
                record.absent_penalty = 0.0

    @api.depends('base_salary', 'total_allowance', 'total_bonus', 'deduction_ids', 'late_penalty', 'absent_penalty')
    def _compute_total_deduction(self):
        for record in self:
            total_deduction = sum(
                record.base_salary * (d.rate / 100) if d.salary_type == 'base_salary'
                else (record.base_salary + record.total_allowance + record.total_bonus) * (d.rate / 100)
                for d in record.deduction_ids if d.rate > 0
            )
            record.total_deduction = total_deduction + record.late_penalty + record.absent_penalty if record.late_penalty is not None and record.absent_penalty is not None else 0.0

    @api.depends('total_salary', 'total_deduction')
    def _compute_total_salary_after_deduction(self):
        for record in self:
            record.total_salary_after_deduction = record.total_salary - record.total_deduction if record.total_salary is not None and record.total_deduction is not None else 0.0

    @api.depends('total_salary_after_deduction')
    def _compute_tax(self):
        for record in self:
            threshold = 11000000  # 11 triệu
            tax_rate = 0.1  # 10%
            record.tax = max(0, (
                        record.total_salary_after_deduction - threshold) * tax_rate) if record.total_salary_after_deduction else 0.0

    @api.depends('total_salary_after_deduction', 'tax')
    def _compute_net_salary(self):
        for record in self:
            record.net_salary = record.total_salary_after_deduction - record.tax if record.total_salary_after_deduction is not None and record.tax is not None else 0.0

    @api.depends('staff_id', 'sheet_id.month', 'sheet_id.year')
    def _compute_work_days(self):
        for record in self:
            if record.staff_id and record.sheet_id:
                month = int(record.sheet_id.month)
                year = int(record.sheet_id.year)
                attendances = record.staff_id.attendance_ids.filtered(
                    lambda a: a.date.month == month and a.date.year == year and a.status != 'absent'
                )
                record.work_days = len(attendances)
            else:
                record.work_days = 0.0

    @api.depends('staff_id', 'sheet_id.month', 'sheet_id.year')
    def _compute_late_days(self):
        for record in self:
            if record.staff_id and record.sheet_id:
                month = int(record.sheet_id.month)
                year = int(record.sheet_id.year)
                attendances = record.staff_id.attendance_ids.filtered(
                    lambda a: a.date.month == month and a.date.year == year and a.status == 'late'
                )
                record.late_days = len(attendances)
            else:
                record.late_days = 0.0

    @api.depends('staff_id', 'sheet_id.month', 'sheet_id.year')
    def _compute_absent_days(self):
        for record in self:
            if record.staff_id and record.sheet_id:
                month = int(record.sheet_id.month)
                year = int(record.sheet_id.year)
                attendances = record.staff_id.attendance_ids.filtered(
                    lambda a: a.date.month == month and a.date.year == year
                )
                total_possible_days = len(set(a.date for a in attendances)) if attendances else 0
                record.absent_days = max(0, record.standard_work_days - total_possible_days)
            else:
                record.absent_days = 0.0

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_pay(self):
        self.write({'state': 'paid'})


# Model quản lý phụ cấp (giữ nguyên)
class StaffSalaryAllowance(models.Model):
    _name = 'clinic.staff.salary.allowance'
    _description = 'Clinic Staff Salary Allowance'

    name = fields.Char(string='Loại phụ cấp', required=True)
    amount = fields.Float(string='Số tiền phụ cấp (VNĐ)', required=True)
    note = fields.Text(string='Ghi chú')


# Model quản lý thưởng (giữ nguyên)
class StaffSalaryBonus(models.Model):
    _name = 'clinic.staff.salary.bonus'
    _description = 'Clinic Staff Salary Bonus'

    name = fields.Char(string='Loại thưởng', required=True)
    amount = fields.Float(string='Số tiền thưởng (VNĐ)', required=True)
    reason = fields.Text(string='Lý do')


# Model quản lý khấu trừ (giữ nguyên)
class StaffSalaryDeduction(models.Model):
    _name = 'clinic.staff.salary.deduction'
    _description = 'Clinic Staff Salary Deduction'

    name = fields.Char(string='Loại khấu trừ', required=True)
    rate = fields.Float(string='Tỷ lệ (%)', default=0.0)
    salary_type = fields.Selection([
        ('base_salary', 'Lương cơ bản'),
        ('total_salary', 'Tổng lương')
    ], string='Loại lương áp dụng', required=True, default='base_salary')
    reason = fields.Text(string='Lý do khấu trừ')
