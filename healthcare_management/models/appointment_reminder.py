from odoo import models, fields, api
from datetime import datetime, timedelta


class AppointmentReminder(models.Model):
    _name = 'appointment.reminder'
    _description = 'Quản lý thông báo lịch hẹn'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên', related='appointment_id.name', store=True)
    appointment_id = fields.Many2one('clinic.appointment', string='Lịch hẹn', required=True, ondelete='cascade')
    patient_id = fields.Many2one(related='appointment_id.patient_id', string='Bệnh nhân', store=True)
    appointment_date = fields.Datetime(related='appointment_id.appointment_date', string='Ngày giờ hẹn', store=True)
    notification_date = fields.Datetime(string='Ngày gửi thông báo', compute='_compute_notification_date', store=True)
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
        if appointment.state == 'draft':
            self.create({
                'appointment_id': appointment.id,
            })

    @api.model
    def _cron_send_appointment_reminders(self):
        """Hàm gửi thông báo lịch hẹn tự động"""
        today = fields.Datetime.now()
        tomorrow = today + timedelta(days=1)

        # Tìm các thông báo cần gửi (thời gian thông báo nằm giữa hiện tại và ngày mai)
        reminders = self.search([
            ('state', '=', 'to_send'),
            ('notification_date', '>=', today),
            ('notification_date', '<=', tomorrow),
            ('appointment_id.state', '=', 'draft')
        ])

        for reminder in reminders:
            self._send_reminder_email(reminder)

    def _send_reminder_email(self, reminder):
        """Gửi email thông báo cho lịch hẹn"""
        try:
            email_template = self.env.ref('appointment_reminder.appointment_reminder_email_template')
            email_template.send_mail(reminder.id, force_send=True)
            reminder.write({'state': 'sent', 'email_status': 'Email đã được gửi thành công'})
            reminder.appointment_id.action_confirm()

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