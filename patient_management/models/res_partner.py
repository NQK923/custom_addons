from odoo import models, fields, api
from datetime import datetime,date

class ResPartner(models.Model):

    _inherit="res.partner"

    age = fields.Integer(
        string="Tuổi",
        compute="_compute_age",
        inverse="_inverse_age"
    )
    date_of_birth =  fields.Date(
        string="Ngày sinh"
    )
    gender = fields.Selection(
        string="Giới tính",
        selection=[
            ('male', 'Nam'),
            ('female', 'Nữ'),
            ('other', 'Khác')
        ],
        required=True,
        default="other"
    )
    pathology_ids = fields.Many2many(
        string="Pathologies",
        comodel_name="pathology",
        relation="partner_pathology_rel",
        column1="partner_id",
        column2="pathology_id",
    )




    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            today = date.today()
            if record.date_of_birth:
                record.age = today.year - record.date_of_birth.year
            else:
                record.age = 0
    def _inverse_age(self):
        for record in self:
            if record.age > 0:
                today = date.today()
                year = today.year - record.age
                record.date_of_birth = date(year,today.month,today.day)
            else:
                record.date_of_birth = False
