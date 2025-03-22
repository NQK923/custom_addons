# appointment_reminder/models/hooks.py
from odoo import models, api


class ClinicAppointment(models.Model):
    _inherit = 'clinic.appointment'

    @api.model_create_multi
    def create(self, vals_list):
        appointments = super().create(vals_list)

        for appointment in appointments:
            self.env['appointment.reminder'].create_from_appointment(appointment)

        return appointments

    def write(self, vals):
        result = super(ClinicAppointment, self).write(vals)

        if 'appointment_date' in vals:
            for record in self:
                reminder = self.env['appointment.reminder'].search([
                    ('note', '=', record.id),
                    ('state', 'in', ['to_send', 'failed'])
                ], limit=1)

                if not reminder:
                    self.env['appointment.reminder'].create_from_appointment(record)

        return result