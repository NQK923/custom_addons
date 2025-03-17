
from odoo import models, fields, api

class PharmacyProduct(models.Model):
    _name = 'pharmacy.product'
    _description = 'Pharmacy Product'

    name = fields.Char(string='Tên thuốc', required=True)
    code = fields.Char(string='Mã thuốc', required=True)
    category = fields.Char(string='Loại thuốc')
    manufacturer = fields.Char(string='Nhà sản xuất')
    unit_price = fields.Float(string='Đơn giá')
    quantity = fields.Float(string='Số lượng tồn kho')
    date = fields.Datetime(string='Ngày sản xuất')
    expiry = fields.Datetime(string='Hạn sử dụng')
    description = fields.Text(string='Mô tả')

from odoo.exceptions import ValidationError

class PharmacyStockMove(models.Model):
    _name = 'pharmacy.stock.move'
    _description = 'Pharmacy Stock Move'

    product_id = fields.Many2one('pharmacy.product', string='Medicine', required=True)
    move_type = fields.Selection([
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
    ], string='Move Type', required=True)
    quantity = fields.Float(string='Số lượng', required=True)
    date = fields.Datetime(string='Thời gian', default=fields.Datetime.now)
    note = fields.Text(string='Ghi chú')

    @api.model
    def create(self, vals):
        record = super(PharmacyStockMove, self).create(vals)
        if record.move_type == 'in':
            record.product_id.quantity += record.quantity
        elif record.move_type == 'out':
            if record.product_id.quantity < record.quantity:
                raise ValidationError('Không đủ số lượng tồn kho để xuất.')
            record.product_id.quantity -= record.quantity
        return record

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError('Số lượng phải lớn hơn 0.')
fields.Text(string='Note')




class PrescriptionOrder(models.Model):
    _name = 'prescription.order'
    _description = 'Prescription Order'

    name = fields.Char(string='Đơn thuốc', required=True, copy=False, readonly=True, default='New')
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True)
    staff_id = fields.Many2one('clinic.staff', string="Bác sĩ")
    prescription_line_ids = fields.One2many('prescription.line', 'order_id', string='Dòng thuốc theo toa')
    numdate = fields.Float(string='Số Ngày uống', required=True)
    date = fields.Datetime(string='Thời gian', default=fields.Datetime.now)
    notes = fields.Text(string='Ghi chú')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('prescription.order') or 'New'
        return super(PrescriptionOrder, self).create(vals)

class PrescriptionLine(models.Model):
    _name = 'prescription.line'
    _description = 'Prescription Line'

    order_id = fields.Many2one('prescription.order', string='Mã đơn hàng', required=True)
    product_id = fields.Many2one('pharmacy.product', string='Mã sản phẩm', required=True)
    quantity = fields.Float(string='Số lượng', required=True)
    dosage = fields.Char(string='Liều lượng/ngày/bữa', required=True)
    instructions = fields.Text(string='Hướng dẫn')

    @api.constrains('product_id', 'order_id')
    def _check_drug_interactions(self):
        for record in self:
            existing_products = self.env['prescription.line'].search([
                ('order_id', '=', record.order_id.id),
                ('id', '!=', record.id)
            ]).mapped('product_id')

            for product in existing_products:
                if product.id == record.product_id.id:
                    raise models.ValidationError(
                        f"Thuốc {product.name} đã tồn tại trong đơn thuốc!"
                    )
