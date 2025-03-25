from odoo import models, fields, api


class ClinicPatient(models.Model):
    _inherit = "clinic.patient"

    treatment_plan_ids = fields.One2many(
        string="Lịch sử khám",
        comodel_name="treatment.plan",
        inverse_name="patient_id"
    )
