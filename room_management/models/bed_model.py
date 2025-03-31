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
        store=True
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
                if record.patient_id.patient_type == "inpatient":
                    record.patient_id.patient_type = "outpatient"

    @api.constrains('patient_id')
    def _constrains_patient_id(self):
        for record in self:
            if record.patient_id:
                patient_record = self.env['clinic.bed'].search(
                    [
                        ('patient_id', '=', record.patient_id.id),
                        ('id', '!=', record.id)
                    ]
                )
                if patient_record:
                    raise ValidationError("Bệnh nhân đã có giường")


    # Nút xuất viện
    def action_out(self):
        self.ensure_one()
        if self.patient_id:
            self.patient_id.patient_type = 'outpatient'
            self.patient_id = False