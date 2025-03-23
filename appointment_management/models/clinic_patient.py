from odoo import models, fields, api

class ClinicPatient(models.Model):

    _inherit = "clinic.patient"

    appointment_ids = fields.One2many(
        string="Appointments",
        comodel_name="clinic.appointment",
        inverse_name="patient_id",
    )