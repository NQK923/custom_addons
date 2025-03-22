# appointment_reminder/models/hooks.py
from odoo import models, api


class ClinicAppointment(models.Model):
    _inherit = 'clinic.appointment'

    @api.model_create_multi
    def create(self, vals_list):
        appointments = super().create(vals_list)

        # Tạo reminder cho các lịch hẹn mới
        for appointment in appointments:
            self.env['appointment.reminder'].create_from_appointment(appointment)

        return appointments