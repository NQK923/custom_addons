from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicRoom(models.Model):
    _name = 'clinic.room'
    _description = 'Phòng khám'

    name = fields.Char(string='Tên phòng', required=True)
    room_type = fields.Selection([
        ('exam', 'Phòng khám'),
        ('treatment', 'Phòng điều trị'),
        ('emergency', 'Phòng cấp cứu')
    ], string='Loại phòng', required=True)
    capacity = fields.Integer(string='Sức chứa')
    status = fields.Selection(
        [
            ('available', 'Còn trống'),
            ('occupied', 'Đã đầy'),
        ],
        string='Trạng thái',
        default='available',
        compute="_compute_status",
        required=True,
    )
    bed_ids = fields.One2many(
        comodel_name='clinic.bed',
        inverse_name='room_id',
        string='Danh sách giường',
        compute="_compute_bed_ids",
        store=True,
        readonly=False,
    )
    note = fields.Text(string='Ghi chú')

    @api.constrains('capacity')
    def _constrains_capacity(self):
        for record in self:
            if record.capacity < 1:
                raise ValidationError("Sức chứa không hợp lệ")

    @api.depends('bed_ids.status')
    def _compute_status(self):
        for record in self:
            if record.bed_ids:
                if any(record.bed_ids.filtered(lambda r: r.status == 'available')):
                    record.status = 'available'
                else:
                    record.status = 'occupied'
            else:
                record.status = 'available'

    @api.depends('capacity')
    def _compute_bed_ids(self):
        context = self.env.context
        active_id = context.get('params', {}).get('resId', False)
        for record in self:
            if record.capacity >= 1:
                bed_vals = [dict(status='available', room_id=active_id) for i in range(record.capacity)]
                bed_ids = self.env['clinic.bed'].create(bed_vals)
                record.write(
                    {
                        'bed_ids': [(6, 0, bed_ids.ids)]
                    }
                )
            else:
                record.bed_ids = False
