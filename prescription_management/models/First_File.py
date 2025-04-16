import uuid

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicService(models.Model):
    _name = 'clinic.service'
    _description = 'Dịch vụ phòng khám'
    _rec_name = 'service_name'

    name = fields.Char(string='Mã dịch vụ', required=True, copy=False, readonly=True, default='New')
    service_name = fields.Char(string='Tên dịch vụ', required=True)
    price = fields.Float(string='Giá dịch vụ', required=True)
    description = fields.Text(string='Mô tả')
    active = fields.Boolean(default=True)
    insurance_covered = fields.Boolean(string='Được bảo hiểm chi trả', default=False)  # Thêm trường này

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)


class PharmacyProduct(models.Model):
    _name = 'pharmacy.product'
    _description = 'Dược phẩm'
    _rec_name = 'display_name'

    display_name = fields.Char(string='Tên thuốc', compute='_compute_display_name', store=True)
    name = fields.Char(string='Tên thuốc', required=True)
    code = fields.Char(string='Mã thuốc', required=True)
    category = fields.Char(string='Loại thuốc')
    manufacturer = fields.Char(string='Nhà sản xuất')
    quantity = fields.Integer(string='Số lượng tồn kho', default=0)
    is_quantity = fields.Boolean(string="Cảnh báo tồn kho", compute='_compute_is_quantity', store=True)
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
    insurance_covered = fields.Boolean(string='Được bảo hiểm chi trả', default=False)  # Thêm trường này

    @api.depends('quantity')
    def _compute_is_quantity(self):
        for record in self:
            record.is_quantity = record.quantity < 10

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} - {record.name}"

    @api.constrains('purchase_price', 'unit_price')
    def _check_prices(self):
        for record in self:
            if record.purchase_price <= 0:
                raise ValidationError('Giá nhập phải lớn hơn 0!')
            if record.unit_price <= 0:
                raise ValidationError('Giá bán phải lớn hơn 0!')
            if record.unit_price < record.purchase_price:
                raise ValidationError('Giá bán phải lớn hơn hoặc bằng giá nhập!')

            # Kiểm tra mức thặng số tối đa theo quy định
            max_profit_margin = self._get_max_profit_margin(record.purchase_price)
            actual_profit_margin = ((record.unit_price - record.purchase_price) / record.purchase_price) * 100
            if actual_profit_margin > max_profit_margin:
                raise ValidationError(
                    f"Giá bán vượt quá mức thặng số tối đa cho phép ({max_profit_margin}%)! "
                    f"Giá bán tối đa cho phép là {record.purchase_price * (1 + max_profit_margin / 100)} VNĐ."
                )

    def _get_max_profit_margin(self, purchase_price):
        """Tính mức thặng số tối đa theo quy định."""
        if purchase_price <= 1000:
            return 15.0  # 15%
        elif 1000 < purchase_price <= 5000:
            return 10.0  # 10%
        elif 5000 < purchase_price <= 100000:
            return 7.0  # 7%
        elif 100000 < purchase_price <= 1000000:
            return 5.0  # 5%
        else:
            return 2.0  # 2%

    @api.depends('purchase_price', 'unit_price')
    def _compute_profit_margin(self):
        for record in self:
            if record.purchase_price > 0:
                record.profit_margin = ((record.unit_price - record.purchase_price) / record.purchase_price) * 100
            else:
                record.profit_margin = 0.0

    @api.onchange('purchase_price')
    def _onchange_purchase_price(self):
        """Tự động đề xuất giá bán dựa trên mức thặng số tối đa."""
        if self.purchase_price:
            max_profit_margin = self._get_max_profit_margin(self.purchase_price)
            self.unit_price = self.purchase_price * (1 + max_profit_margin / 100)


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

    @api.constrains('quantity', 'product_id')
    def _check_inventory(self):
        for record in self:
            if record.quantity > record.product_id.quantity:
                raise ValidationError(
                    f"Số lượng thuốc {record.product_id.name} vượt quá tồn kho! "
                )
