from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicBed(models.Model):
    _name = 'clinic.bed'
    _description = 'Giường bệnh'

    room_id = fields.Many2one('clinic.room', string='Phòng', required=True)
    status = fields.Selection(
        [
            ('available', 'Còn trống'),
            ('occupied', 'Có bệnh nhân'),
        ],
        string='Trạng thái',
        default='available',
        compute="_compute_status",
        stored=True
    )
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

    @api.constrains('patient_id')
    def _constrains_patient_id(self):
        for record in self:
            if record.patient_id:
                patient_record = self.env['clinic.bed'].search(
                    [
                        ('patient_id', '=', record.patient_id.id),
                        # ('room_id', '=', record.room_id.id)
                    ]
                )
                if len(patient_record) > 1:
                    raise ValidationError("Bệnh nhân đã có giường")


    # Nut xuat vien
    def action_out(self):
        self.ensure_one()
        self.patient_id.patient_type = 'outpatient'
        self.patient_id = False