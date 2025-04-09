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

    @api.model_create_multi
    def create(self, vals_list):
        rooms = super(ClinicRoom, self).create(vals_list)
        # Tạo giường sau khi phòng đã được tạo và có ID
        for room in rooms:
            if room.capacity >= 1:
                bed_vals = []
                for i in range(room.capacity):
                    bed_vals.append({
                        'status': 'available',
                        'room_id': room.id
                    })
                self.env['clinic.bed'].create(bed_vals)
        return rooms

    def write(self, vals):
        old_capacity = {room.id: room.capacity for room in self}
        result = super(ClinicRoom, self).write(vals)

        # Xử lý thay đổi sức chứa
        if 'capacity' in vals:
            for room in self:
                current_beds = len(room.bed_ids)
                # Nếu tăng sức chứa, thêm giường mới
                if room.capacity > current_beds:
                    bed_vals = []
                    for i in range(current_beds, room.capacity):
                        bed_vals.append({
                            'status': 'available',
                            'room_id': room.id
                        })
                    self.env['clinic.bed'].create(bed_vals)
                # Nếu giảm sức chứa, xóa giường trống
                elif room.capacity < current_beds:
                    empty_beds = room.bed_ids.filtered(lambda b: not b.patient_id)
                    if len(empty_beds) >= (current_beds - room.capacity):
                        # Xóa số giường trống cần thiết
                        beds_to_remove = empty_beds[:(current_beds - room.capacity)]
                        beds_to_remove.unlink()
                    else:
                        # Nếu không đủ giường trống, reset về capacity cũ và hiển thị lỗi
                        room.capacity = old_capacity[room.id]
                        raise ValidationError("Không thể giảm sức chứa vì có bệnh nhân đang sử dụng giường")

        return result
