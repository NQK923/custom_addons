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

    def _check_can_send_email(self):
        """Kiểm tra xem có thể gửi email không"""
        self.ensure_one()
        if not self.patient_id:
            return False, "Không tìm thấy thông tin bệnh nhân"

        if not self.patient_id.email:
            return False, "Bệnh nhân không có địa chỉ email"

        if not self.appointment_date:
            return False, "Không có thông tin ngày giờ hẹn"

        return True, "Có thể gửi email"

    @api.model
    def _cron_send_appointment_reminders(self):
        """Hàm gửi thông báo lịch hẹn tự động"""
        today = fields.Datetime.now()
        tomorrow = today + timedelta(days=1)

        appointments = self.env['clinic.appointment'].search([
            ('appointment_date', '>=', today + timedelta(days=1)),
            ('appointment_date', '<=', today + timedelta(days=7)),
            ('patient_id.email', '!=', False)
        ])

        for appointment in appointments:
            existing = self.search([('appointment_id', '=', appointment.id)], limit=1)
            if not existing:
                self.create({
                    'appointment_id': appointment.id,
                })

        reminders = self.search([
            ('state', '=', 'to_send'),
            ('notification_date', '>=', today),
            ('notification_date', '<=', tomorrow),
            ('patient_id.email', '!=', False)
        ])

        for reminder in reminders:
            self._send_reminder_email(reminder)

    def _send_reminder_email(self):
        """Gửi email thông báo cho lịch hẹn"""
        try:
            import logging
            from odoo.tools import formataddr
            import html

            _logger = logging.getLogger(__name__)
            _logger.info(f"Attempting to send appointment reminder email to {self.patient_id.email}")

            if not self.patient_id.email:
                self.write({
                    'state': 'failed',
                    'email_status': 'Không thể gửi email: Bệnh nhân không có địa chỉ email'
                })
                return False

            # Get company information
            company = self.env.company
            company_email = company.email or 'noreply@example.com'

            # Format appointment date - attempt to format as in the template
            appointment_date = self.appointment_date
            formatted_date = appointment_date.strftime("%d/%m/%Y %H:%M:%S")
            try:
                user_tz = self.env.user.tz
                if user_tz:
                    from pytz import timezone
                    user_timezone = timezone(user_tz)
                    appointment_date_tz = appointment_date.astimezone(user_timezone)
                    formatted_date = appointment_date_tz.strftime("%d/%m/%Y %H:%M:%S")
            except Exception as e:
                _logger.warning(f"Error formatting date with timezone: {str(e)}")

            # Create email body
            subject = "Nhắc nhở: Lịch hẹn khám"
            body_html = f"""
            <div style="margin: 0px; padding: 0px; font-size: 13px;">
                <p style="margin: 0px; padding: 0px; font-size: 13px;">
                    Kính gửi {html.escape(self.patient_id.name or 'Quý khách')},
                </p>
                <p style="margin: 0px; padding: 0px; font-size: 13px;">
                    Chúng tôi xin gửi lời nhắc nhở về lịch hẹn khám sắp tới của bạn:
                </p>
                <ul>
                    <li>Mã lịch hẹn: <strong>{html.escape(self.name or '')}</strong></li>
                    <li>Thời gian: <strong>{formatted_date}</strong></li>
                    <li>Bác sĩ: <strong>{html.escape(self.staff_id.staff_name or 'Chưa xác định')}</strong></li>
                    <li>Phòng khám: <strong>{html.escape(self.room_id.name or 'Chưa xác định')}</strong></li>
                </ul>
                <p style="margin: 0px; padding: 0px; font-size: 13px;">
                    Vui lòng đến trước 15 phút để hoàn tất thủ tục.
                </p>
                <p style="margin: 0px; padding: 0px; font-size: 13px;">
                    Nếu bạn cần thay đổi lịch hẹn, vui lòng liên hệ với chúng tôi trước ít nhất 24 giờ.
                </p>
                <p style="margin: 0px; padding: 0px; font-size: 13px;">
                    Trân trọng,<br/>
                    Phòng khám {html.escape(company.name or '')}
                </p>
            </div>
            """

            # Create mail values
            mail_values = {
                'subject': subject,
                'body_html': body_html,
                'email_from': formataddr((company.name, company_email)) if company.name else company_email,
                'email_to': self.patient_id.email,
                'auto_delete': True,
            }

            # Create and send the mail
            mail = self.env['mail.mail'].sudo().create(mail_values)
            _logger.info(f"Created mail.mail record with ID: {mail.id}")

            mail.send(raise_exception=False)
            _logger.info(f"Mail send attempted for ID: {mail.id}")

            # Check mail state
            mail.refresh()
            _logger.info(f"Mail state after sending: {mail.state}")

            if mail.state == 'sent' or mail.state == 'outgoing':
                self.write({'state': 'sent', 'email_status': 'Email đã được gửi thành công'})
                return True
            else:
                self.write({'state': 'failed', 'email_status': f'Lỗi khi gửi email: Trạng thái email {mail.state}'})
                return False

        except Exception as e:
            import traceback
            _logger.error(f"Error sending appointment reminder email: {str(e)}")
            _logger.error(traceback.format_exc())
            self.write({'state': 'failed', 'email_status': f'Lỗi khi gửi email: {str(e)}'})
            return False

    def action_send_reminder_now(self):
        """Hành động gửi thông báo ngay lập tức"""
        self.ensure_one()
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Call the email sending method
            _logger.info(f"Sending reminder for appointment {self.name}")
            result = self._send_reminder_email()
            if result:
                _logger.info(f"Successfully sent reminder for appointment {self.name}")
                return True
            else:
                _logger.error(f"Failed to send reminder for appointment {self.name}")
                return False
        except Exception as e:
            import traceback
            _logger.error(f"Exception when sending reminder: {str(e)}")
            _logger.error(traceback.format_exc())
            self.write({
                'state': 'failed',
                'email_status': f'Lỗi khi gửi email: {str(e)}'
            })
            return False

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