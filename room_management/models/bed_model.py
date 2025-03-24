from odoo import models, fields, api


class ClinicBed(models.Model):
    _name = 'clinic.bed'
    _description = 'Giường bệnh'

    room_id = fields.Many2one('clinic.room', string='Phòng', required=True)
    status = fields.Selection(
        [
            ('available', 'Còn trống'),
            ('occupied', 'Có bệnh nhân'),
            ('maintenance', 'Bảo trì')
        ],
        string='Trạng thái',
        default='available',
        compute="_compute_status",
        stored=True)
    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string='Bệnh nhân'
    )
    patient_name = fields.Char(
        related="patient_id.name"
    )

    @api.depends("patient_id")
    def _compute_status(self):
        for record in self:
            if record.patient_id:
                record.status = "occupied"
                record.patient_id.patient_type = "inpatient"
            else:
                record.status = "available"
                record.patient_id.patient_type = "outpatient"
