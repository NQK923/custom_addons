from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class ClinicAppointment(models.Model):
    _name = 'clinic.appointment'
    _description = 'Lịch hẹn khám'
    _rec_name = 'name'

    name = fields.Char(string='Mã lịch hẹn', required=True, copy=False, readonly=True, default='New')
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True)
    appointment_date = fields.Datetime(string='Ngày giờ hẹn', required=True)
    staff_id = fields.Many2one('clinic.staff', string='Bác sĩ', required=True,
                               domain=[('staff_type', '=', 'Bác sĩ')])
    room_id = fields.Many2one('clinic.room', string='Phòng khám',
                              domain=[('room_type', '=', 'exam')])
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', required=True)
    note = fields.Text(string='Ghi chú')
    patient_name = fields.Char(
        related="patient_id.name"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('clinic.appointment') or 'New'

            # Validate appointment date before creation
            if 'appointment_date' in vals:
                appointment_date = fields.Datetime.from_string(vals['appointment_date'])
                tomorrow = datetime.now() + timedelta(days=1)
                tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

                if appointment_date < tomorrow:
                    raise ValidationError(
                        "Không thể đặt lịch hẹn trong quá khứ hoặc hôm nay. Vui lòng chọn ngày mai hoặc sau đó!")

            # Validate doctor availability before creation
            if 'staff_id' in vals and 'appointment_date' in vals:
                staff_id = vals['staff_id']
                appointment_date = fields.Datetime.from_string(vals['appointment_date'])
                one_hour_before = appointment_date - timedelta(hours=1)
                one_hour_after = appointment_date + timedelta(hours=1)

                domain = [
                    ('staff_id', '=', staff_id),
                    ('appointment_date', '>=', one_hour_before),
                    ('appointment_date', '<=', one_hour_after),
                    ('state', 'not in', ['cancelled']),
                ]

                if self.search_count(domain) > 0:
                    staff = self.env['clinic.staff'].browse(staff_id)
                    raise ValidationError(
                        f"Bác sĩ {staff.name} đã có lịch hẹn khác trong vòng 1 tiếng của thời điểm này!")

            # Validate room availability before creation
            if 'room_id' in vals and vals['room_id'] and 'appointment_date' in vals:
                room_id = vals['room_id']
                appointment_date = fields.Datetime.from_string(vals['appointment_date'])
                one_hour_before = appointment_date - timedelta(hours=1)
                one_hour_after = appointment_date + timedelta(hours=1)

                domain = [
                    ('room_id', '=', room_id),
                    ('appointment_date', '>=', one_hour_before),
                    ('appointment_date', '<=', one_hour_after),
                    ('state', 'not in', ['cancelled']),
                ]

                if self.search_count(domain) > 0:
                    room = self.env['clinic.room'].browse(room_id)
                    raise ValidationError(f"Phòng {room.name} đã được đặt trong vòng 1 tiếng của thời điểm này!")

        return super().create(vals_list)

    def write(self, vals):
        # Validate appointment date before update
        if 'appointment_date' in vals:
            appointment_date = fields.Datetime.from_string(vals['appointment_date'])
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

            if appointment_date < tomorrow:
                raise ValidationError(
                    "Không thể cập nhật lịch hẹn vào quá khứ hoặc hôm nay. Vui lòng chọn ngày mai hoặc sau đó!")

        # Validate doctor availability before update
        if ('staff_id' in vals or 'appointment_date' in vals) and (self.staff_id or 'staff_id' in vals):
            staff_id = vals.get('staff_id', self.staff_id.id)
            appointment_date = fields.Datetime.from_string(
                vals['appointment_date']) if 'appointment_date' in vals else self.appointment_date
            one_hour_before = appointment_date - timedelta(hours=1)
            one_hour_after = appointment_date + timedelta(hours=1)

            domain = [
                ('staff_id', '=', staff_id),
                ('appointment_date', '>=', one_hour_before),
                ('appointment_date', '<=', one_hour_after),
                ('state', 'not in', ['cancelled']),
                ('id', '!=', self.id)
            ]

            if self.search_count(domain) > 0:
                staff_name = self.env['clinic.staff'].browse(staff_id).name if isinstance(staff_id,
                                                                                          int) else self.staff_id.name
                raise ValidationError(f"Bác sĩ {staff_name} đã có lịch hẹn khác trong vòng 1 tiếng của thời điểm này!")

        # Validate room availability before update
        if ('room_id' in vals or 'appointment_date' in vals) and (self.room_id or 'room_id' in vals):
            room_id = vals.get('room_id', self.room_id.id if self.room_id else False)
            if room_id:
                appointment_date = fields.Datetime.from_string(
                    vals['appointment_date']) if 'appointment_date' in vals else self.appointment_date
                one_hour_before = appointment_date - timedelta(hours=1)
                one_hour_after = appointment_date + timedelta(hours=1)

                domain = [
                    ('room_id', '=', room_id),
                    ('appointment_date', '>=', one_hour_before),
                    ('appointment_date', '<=', one_hour_after),
                    ('state', 'not in', ['cancelled']),
                    ('id', '!=', self.id)
                ]

                if self.search_count(domain) > 0:
                    room_name = self.env['clinic.room'].browse(room_id).name if isinstance(room_id,
                                                                                           int) else self.room_id.name
                    raise ValidationError(f"Phòng {room_name} đã được đặt trong vòng 1 tiếng của thời điểm này!")

        return super().write(vals)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.constrains('appointment_date')
    def _check_appointment_date(self):
        for record in self:
            if record.appointment_date:
                # Require appointments to be at least for tomorrow
                tomorrow = datetime.now() + timedelta(days=1)
                tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

                if record.appointment_date < tomorrow:
                    raise ValidationError(
                        "Không thể đặt lịch hẹn trong quá khứ hoặc hôm nay. Vui lòng chọn ngày mai hoặc sau đó!")

    @api.constrains('staff_id', 'appointment_date')
    def _check_doctor_availability(self):
        for record in self:
            one_hour_before = record.appointment_date - timedelta(hours=1)
            one_hour_after = record.appointment_date + timedelta(hours=1)
            domain = [
                ('staff_id', '=', record.staff_id.id),
                ('appointment_date', '>=', one_hour_before),
                ('appointment_date', '<=', one_hour_after),
                ('state', 'not in', ['cancelled']),
                ('id', '!=', record.id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(
                    f"Bác sĩ {record.staff_id.name} đã có lịch hẹn khác trong vòng 1 tiếng của thời điểm này!")

    @api.constrains('room_id', 'appointment_date')
    def _check_room_availability(self):
        for record in self:
            if record.room_id:
                one_hour_before = record.appointment_date - timedelta(hours=1)
                one_hour_after = record.appointment_date + timedelta(hours=1)

                domain = [
                    ('room_id', '=', record.room_id.id),
                    ('appointment_date', '>=', one_hour_before),
                    ('appointment_date', '<=', one_hour_after),
                    ('state', 'not in', ['cancelled']),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        f"Phòng {record.room_id.name} đã được đặt trong vòng 1 tiếng của thời điểm này!")