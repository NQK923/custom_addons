from odoo import models, fields, api

class ClinicBed(models.Model):
    _name = 'clinic.bed'
    _description = 'Giường bệnh'

    name = fields.Char(string='Tên giường', required=True)
    room_id = fields.Many2one('clinic.room', string='Phòng', required=True)
    status = fields.Selection([
        ('available', 'Còn trống'),
        ('occupied', 'Có bệnh nhân'),
        ('maintenance', 'Bảo trì')
    ], string='Trạng thái', default='available')
    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string='Bệnh nhân'
    )
    patient_name = fields.Char(
        related="patient_id.name"
    )