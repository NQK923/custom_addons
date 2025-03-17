from odoo import models, fields, api

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
    status = fields.Selection([
        ('available', 'Còn trống'),
        ('occupied', 'Đã có bệnh nhân'),
        ('maintenance', 'Bảo trì')
    ], string='Trạng thái', default='available')
    bed_ids = fields.One2many('clinic.bed', 'room_id', string='Danh sách giường')
    note = fields.Text(string='Ghi chú') 