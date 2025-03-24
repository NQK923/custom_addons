from odoo import fields, models, api, _


class Pathology(models.Model):

    _name = "pathology"
    _description = "Bệnh lý"
    _rec_name = 'name'

    name = fields.Char(
        string="Bệnh lý",
        required=True,
    )