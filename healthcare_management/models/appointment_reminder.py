from odoo import models, fields, api
from datetime import datetime, timedelta


class AppointmentReminder(models.Model):
    _name = 'appointment.reminder'
    _description = 'Quản lý thông báo lịch hẹn'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    appointment_id = fields.Many2one('clinic.appointment', string='Lịch hẹn', required=True, ondelete='cascade')
    name = fields.Char(string='Tên', related='appointment_id.name', store=True)
    patient_id = fields.Many2one(related='appointment_id.patient_id', string='Bệnh nhân', store=True)
    appointment_date = fields.Datetime(related='appointment_id.appointment_date', string='Ngày giờ hẹn', store=True)
    notification_date = fields.Datetime(string='Ngày gửi thông báo', compute='_compute_notification_date', store=True)
    staff_id = fields.Many2one(related='appointment_id.staff_id', string='Bác sĩ', store=True)
    room_id = fields.Many2one(related='appointment_id.room_id', string='Phòng khám', store=True)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)
    state = fields.Selection([
        ('to_send', 'Chờ gửi'),
        ('sent', 'Đã gửi'),
        ('failed', 'Thất bại'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái thông báo', default='to_send', tracking=True)
    email_status = fields.Text(string='Trạng thái email', readonly=True)

    @api.depends('appointment_date')
    def _compute_notification_date(self):
        for record in self:
            if record.appointment_date:
                record.notification_date = record.appointment_date - timedelta(days=3)
            else:
                record.notification_date = False

    @api.model
    def create_from_appointment(self, appointment):
        """Tạo bản ghi reminder cho lịch hẹn mới"""
        existing = self.search([('appointment_id', '=', appointment.id)], limit=1)
        if not existing:
            self.create({
                'appointment_id': appointment.id,
            })

    @api.model
    def _cron_send_appointment_reminders(self):
        """Hàm gửi thông báo lịch hẹn tự động"""
        today = fields.Datetime.now()
        tomorrow = today + timedelta(days=1)

        appointments = self.env['clinic.appointment'].search([
            ('appointment_date', '>=', today + timedelta(days=1)),  # Lịch hẹn trong tương lai
            ('appointment_date', '<=', today + timedelta(days=7))  # Trong vòng 7 ngày tới
        ])

        # Tạo reminder cho các lịch hẹn chưa có
        for appointment in appointments:
            existing = self.search([('appointment_id', '=', appointment.id)], limit=1)
            if not existing:
                self.create({
                    'appointment_id': appointment.id,
                })

        reminders = self.search([
            ('state', '=', 'to_send'),
            ('notification_date', '>=', today),
            ('notification_date', '<=', tomorrow)
        ])

        for reminder in reminders:
            self._send_reminder_email(reminder)

    def _send_reminder_email(self, reminder):
        """Gửi email thông báo cho lịch hẹn"""
        try:
            email_template = self.env.ref('healthcare_management.appointment_reminder_email_template')
            email_template.send_mail(reminder.id, force_send=True)
            reminder.write({'state': 'sent', 'email_status': 'Email đã được gửi thành công'})

            return True
        except Exception as e:
            reminder.write({'state': 'failed', 'email_status': f'Lỗi khi gửi email: {str(e)}'})
            return False

    def action_send_reminder_now(self):
        """Hành động gửi thông báo ngay lập tức"""
        for record in self:
            self._send_reminder_email(record)

    def action_cancel_reminder(self):
        """Hủy thông báo"""
        self.write({'state': 'cancelled'})

    def action_sync_all_appointments(self):
        """Đồng bộ tất cả lịch hẹn vào hệ thống thông báo"""
        appointments = self.env['clinic.appointment'].search([
            ('appointment_date', '>=', fields.Datetime.now())  # Chỉ lịch hẹn trong tương lai
        ])

        created_count = 0
        for appointment in appointments:
            existing = self.search([('appointment_id', '=', appointment.id)], limit=1)
            if not existing:
                self.create({
                    'appointment_id': appointment.id,
                })
                created_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Đồng bộ hoàn tất',
                'message': f'Đã tạo {created_count} thông báo lịch hẹn mới',
                'sticky': False,
            }
        }