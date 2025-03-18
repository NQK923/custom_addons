from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PharmacyProduct(models.Model):
    _name = 'pharmacy.product'
    _description = 'Dược phẩm'

    name = fields.Char(string='Tên thuốc', required=True)
    code = fields.Char(string='Mã thuốc', required=True)
    category = fields.Char(string='Loại thuốc')
    manufacturer = fields.Char(string='Nhà sản xuất')
    quantity = fields.Integer(string='Số lượng tồn kho', default=0)
    uom_id = fields.Selection([
        ('pill', 'Viên'),
        ('bottle', 'Chai'),
        ('box', 'Hộp'),
        ('pack', 'Gói'),
        ('tube', 'Ống')
    ], string='Đơn vị tính', required=True)
    purchase_price = fields.Float(string='Giá nhập', required=True)
    unit_price = fields.Float(string='Giá bán', required=True)
    profit_margin = fields.Float(string='Tỷ suất lợi nhuận (%)', compute='_compute_profit_margin', store=True)
    date = fields.Datetime(string='Ngày sản xuất')
    expiry = fields.Datetime(string='Hạn sử dụng')
    description = fields.Text(string='Mô tả')
    active = fields.Boolean(default=True)

    @api.constrains('purchase_price', 'unit_price')
    def _check_prices(self):
        for record in self:
            if record.purchase_price <= 0:
                raise ValidationError('Giá nhập phải lớn hơn 0!')
            if record.unit_price <= 0:
                raise ValidationError('Giá bán phải lớn hơn 0!')
            if record.unit_price < record.purchase_price:
                raise ValidationError('Giá bán phải lớn hơn hoặc bằng giá nhập!')

    @api.depends('purchase_price', 'unit_price')
    def _compute_profit_margin(self):
        for record in self:
            if record.purchase_price > 0:
                record.profit_margin = ((record.unit_price - record.purchase_price) / record.purchase_price) * 100
            else:
                record.profit_margin = 0.0

    @api.onchange('purchase_price')
    def _onchange_purchase_price(self):
        """Tự động đề xuất giá bán khi nhập giá mua (với lợi nhuận 20%)"""
        if self.purchase_price:
            self.unit_price = self.purchase_price * 1.2
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
