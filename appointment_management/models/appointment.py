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
        return super().create(vals_list)

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
            if record.appointment_date and record.appointment_date < fields.Datetime.now():
                raise ValidationError("Không thể đặt lịch hẹn trong quá khứ!")

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