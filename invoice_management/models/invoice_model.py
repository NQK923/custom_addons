from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class ClinicService(models.Model):
    _name = 'clinic.service'
    _description = 'Dịch vụ phòng khám'

    name = fields.Char(string='Tên dịch vụ', required=True)
    code = fields.Char(string='Mã dịch vụ', required=True)
    price = fields.Float(string='Giá dịch vụ', required=True)
    description = fields.Text(string='Mô tả')
    active = fields.Boolean(default=True)

class ClinicInvoice(models.Model):
    _name = 'clinic.invoice'
    _description = 'Hóa đơn phòng khám'
    _order = 'invoice_date desc, id desc'

    name = fields.Char(string='Số hóa đơn', required=True, copy=False, readonly=True, 
                      default=lambda self: 'New')
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True)
    prescription_id = fields.Many2one('prescription.order', string='Đơn thuốc', 
                                    domain="[('patient_id', '=', patient_id)]")
    invoice_date = fields.Date(string='Ngày lập', default=fields.Date.today, required=True)
    
    # Thay đổi định nghĩa của service_lines và product_lines
    service_lines = fields.One2many('clinic.invoice.line', 'invoice_id', 
                                   string='Dịch vụ',
                                   domain=[('product_id', '=', False)])
    product_lines = fields.One2many('clinic.invoice.line', 'invoice_id', 
                                   string='Thuốc',
                                   domain=[('service_id', '=', False)])

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', required=True)

    service_amount = fields.Float(string='Tổng tiền dịch vụ', compute='_compute_amounts', store=True)
    medicine_amount = fields.Float(string='Tổng tiền thuốc', compute='_compute_amounts', store=True)
    amount_total = fields.Float(string='Tổng cộng', compute='_compute_amounts', store=True)
    insurance_amount = fields.Float(string='Bảo hiểm chi trả', compute='_compute_amounts', store=True)
    patient_amount = fields.Float(string='Bệnh nhân chi trả', compute='_compute_amounts', store=True)
    note = fields.Text(string='Ghi chú')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('clinic.invoice') or 'New'
        return super(ClinicInvoice, self).create(vals)

    @api.depends('service_lines.price_subtotal', 'product_lines.price_subtotal', 'patient_id')
    def _compute_amounts(self):
        for invoice in self:
            # Tính tổng tiền dịch vụ và thuốc
            invoice.service_amount = sum(line.price_subtotal for line in invoice.service_lines)
            invoice.medicine_amount = sum(line.price_subtotal for line in invoice.product_lines)
            invoice.amount_total = invoice.service_amount + invoice.medicine_amount
            
            # Kiểm tra bảo hiểm hợp lệ
            has_valid_insurance = False
            if invoice.patient_id and invoice.patient_id.insurance_policy_id:
                policy = invoice.patient_id.insurance_policy_id
                if policy.insurance_state == 'valid':
                    has_valid_insurance = True

            # Tính tiền bảo hiểm chi trả và bệnh nhân trả
            if has_valid_insurance:
                invoice.insurance_amount = invoice.amount_total * 0.8  # 80%
                invoice.patient_amount = invoice.amount_total * 0.2    # 20%
            else:
                invoice.insurance_amount = 0
                invoice.patient_amount = invoice.amount_total         # 100%

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        """Reset prescription and invoice lines when patient changes"""
        self.prescription_id = False
        self.service_lines = [(5, 0, 0)]  # Clear service lines
        self.product_lines = [(5, 0, 0)]  # Clear product lines

    @api.onchange('prescription_id')
    def _onchange_prescription_id(self):
        if self.prescription_id:
            # Clear existing product lines first
            self.product_lines = [(5, 0, 0)]
            new_lines = []
            for line in self.prescription_id.prescription_line_ids:
                product = line.product_id
                if not product:
                    continue
                    
                if not product.unit_price:
                    raise ValidationError(
                        f"Thuốc '{product.name}' chưa có đơn giá. Vui lòng thiết lập đơn giá trong 'Pharmacy Product' trước khi sử dụng."
                    )
                if product.unit_price <= 0:
                    raise ValidationError(
                        f"Đơn giá của thuốc '{product.name}' phải lớn hơn 0. Vui lòng cập nhật giá trong 'Pharmacy Product'."
                    )
                    
                new_lines.append((0, 0, {
                    'product_id': product.id,
                    'quantity': line.quantity,
                    'price_unit': product.unit_price,
                }))
                
            self.product_lines = new_lines

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_mark_as_paid(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

class ClinicInvoiceLine(models.Model):
    _name = 'clinic.invoice.line'
    _description = 'Chi tiết hóa đơn'

    invoice_id = fields.Many2one('clinic.invoice', string='Hóa đơn', required=True, ondelete='cascade')
    service_id = fields.Many2one('clinic.service', string='Dịch vụ')
    product_id = fields.Many2one('pharmacy.product', string='Thuốc')
    quantity = fields.Float(string='Số lượng', default=1.0, required=True)
    price_unit = fields.Float(string='Đơn giá')
    price_subtotal = fields.Float(string='Thành tiền', compute='_compute_price_subtotal', store=True)
    insurance_amount = fields.Float(string='Bảo hiểm chi trả', compute='_compute_price_subtotal', store=True)
    patient_amount = fields.Float(string='Bệnh nhân chi trả', compute='_compute_price_subtotal', store=True)

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            if not self.service_id.price:
                raise ValidationError(
                    f"Dịch vụ '{self.service_id.name}' chưa có giá. Vui lòng thiết lập giá trước khi sử dụng."
                )
            self.price_unit = self.service_id.price
            self.product_id = False  # Xóa thuốc nếu chọn dịch vụ
        else:
            self.price_unit = 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.product_id.unit_price:
                raise ValidationError(
                    f"Thuốc '{self.product_id.name}' chưa có đơn giá. Vui lòng thiết lập đơn giá trước khi sử dụng."
                )
            self.price_unit = self.product_id.unit_price
            self.service_id = False  # Xóa dịch vụ nếu chọn thuốc
        else:
            self.price_unit = 0.0

    @api.depends('quantity', 'price_unit', 'invoice_id.patient_id')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit
            
            # Kiểm tra bảo hiểm của bệnh nhân
            has_valid_insurance = False
            if line.invoice_id.patient_id and line.invoice_id.patient_id.insurance_policy_id:
                policy = line.invoice_id.patient_id.insurance_policy_id
                if policy.insurance_state == 'valid':
                    has_valid_insurance = True

            # Tính toán số tiền bảo hiểm và bệnh nhân chi trả
            if has_valid_insurance:
                line.insurance_amount = line.price_subtotal * 0.8
                line.patient_amount = line.price_subtotal * 0.2
            else:
                line.insurance_amount = 0
                line.patient_amount = line.price_subtotal

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError('Số lượng phải lớn hơn 0!')

    @api.constrains('price_unit')
    def _check_price_unit(self):
        for line in self:
            if line.price_unit <= 0:
                raise ValidationError(
                    f"Đơn giá của {line.service_id.name or line.product_id.name} phải lớn hơn 0!"
                )
                
class PharmacyImportOrder(models.Model):
    _name = 'pharmacy.import.order'
    _description = 'Phiếu nhập hàng dược phẩm'
    _order = 'import_date desc, id desc'

    name = fields.Char(string='Số phiếu nhập', required=True, copy=False, readonly=True, 
                       default=lambda self: 'New')
    name_supplier = fields.Char(string='Nhà cung cấp', required=True)  # Thay supplier_id bằng name_supplier
    import_date = fields.Date(string='Ngày nhập', default=fields.Date.today, required=True)
    import_lines = fields.One2many('pharmacy.import.line', 'import_id', string='Chi tiết nhập hàng')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('done', 'Hoàn tất'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', required=True)
    amount_subtotal = fields.Float(string='Tổng tiền thuốc', compute='_compute_amounts', store=True)
    amount_tax = fields.Float(string='Thuế', compute='_compute_amounts', store=True)
    amount_total = fields.Float(string='Tổng cộng', compute='_compute_amounts', store=True)
    note = fields.Text(string='Ghi chú')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('pharmacy.import.order') or 'New'
        return super(PharmacyImportOrder, self).create(vals)

    @api.depends('import_lines.price_subtotal')
    def _compute_amounts(self):
        for order in self:
            amount_subtotal = sum(line.price_subtotal for line in order.import_lines)
            amount_tax = amount_subtotal * 0.1  # 10% VAT
            order.amount_subtotal = amount_subtotal
            order.amount_tax = amount_tax
            order.amount_total = amount_subtotal + amount_tax

    def action_confirm(self):
        """Xác nhận phiếu nhập, cập nhật số lượng tồn kho"""
        for order in self:
            if order.state != 'draft':
                raise ValidationError('Chỉ có thể xác nhận phiếu ở trạng thái Nháp!')
            for line in order.import_lines:
                line.product_id.quantity += line.quantity  # Cập nhật tồn kho
            order.write({'state': 'confirmed'})

    def action_done(self):
        """Hoàn tất phiếu nhập"""
        for order in self:
            if order.state != 'confirmed':
                raise ValidationError('Chỉ có thể hoàn tất phiếu đã xác nhận!')
            order.write({'state': 'done'})

    def action_cancel(self):
        """Hủy phiếu nhập, không xóa hẳn"""
        for order in self:
            if order.state == 'done':
                raise ValidationError('Không thể hủy phiếu đã hoàn tất!')
            if order.state == 'confirmed':
                # Hoàn lại tồn kho khi hủy phiếu đã xác nhận
                for line in order.import_lines:
                    if line.product_id.quantity < line.quantity:
                        raise ValidationError(f'Không đủ tồn kho để hoàn lại {line.product_id.name}!')
                    line.product_id.quantity -= line.quantity
            order.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """Đặt lại phiếu về Nháp"""
        for order in self:
            if order.state == 'cancelled':
                order.write({'state': 'draft'})
            else:
                raise ValidationError('Chỉ có thể đặt lại từ trạng thái Đã hủy!')

class PharmacyImportLine(models.Model):
    _name = 'pharmacy.import.line'
    _description = 'Chi tiết phiếu nhập hàng'

    import_id = fields.Many2one('pharmacy.import.order', string='Phiếu nhập', required=True)
    product_id = fields.Many2one('pharmacy.product', string='Thuốc', required=True)
    quantity = fields.Float(string='Số lượng', default=1.0, required=True)
    price_unit = fields.Float(string='Đơn giá')
    price_subtotal = fields.Float(string='Thành tiền', compute='_compute_price_subtotal', store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.unit_price or 0.0

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError('Số lượng nhập phải lớn hơn 0!')
    
    @api.constrains('price_unit')
    def _check_price_unit(self):
        for line in self:
            if line.price_unit <= 0:
                raise ValidationError(
                    f"Đơn giá của {line.service_id.name or line.product_id.name} phải lớn hơn 0!"
                )

class ClinicInsuranceInvoice(models.Model):
    _name = 'clinic.invoice.insurance'
    _description = 'Hóa đơn bảo hiểm'

    name = fields.Char(string='Số hóa đơn BH', readonly=True, copy=False, default='New')
    date_from = fields.Date(string='Từ ngày', required=True)
    date_to = fields.Date(string='Đến ngày', required=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', required=True)

    invoice_line_ids = fields.One2many('clinic.invoice.insurance.line', 'insurance_invoice_id', string='Chi tiết hóa đơn')
    total_service_amount = fields.Float(string='Tổng tiền dịch vụ', compute='_compute_totals', store=True)
    total_medicine_amount = fields.Float(string='Tổng tiền thuốc', compute='_compute_totals', store=True)
    total_insurance_amount = fields.Float(string='Bảo hiểm chi trả', compute='_compute_totals', store=True)

    @api.depends('invoice_line_ids.service_amount', 'invoice_line_ids.medicine_amount', 'invoice_line_ids.insurance_amount')
    def _compute_totals(self):
        for record in self:
            record.total_service_amount = sum(record.invoice_line_ids.mapped('service_amount'))
            record.total_medicine_amount = sum(record.invoice_line_ids.mapped('medicine_amount'))
            record.total_insurance_amount = sum(record.invoice_line_ids.mapped('insurance_amount'))

    def action_confirm(self):
        for record in self:
            if record.state == 'draft':
                record.state = 'confirmed'

    def action_pay(self):
        for record in self:
            if record.state == 'confirmed':
                record.state = 'paid'

    def action_cancel(self):
        for record in self:
            if record.state in ['draft', 'confirmed']:
                record.state = 'cancelled'

    def action_draft(self):
        for record in self:
            if record.state == 'cancelled':
                record.state = 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('clinic.insurance.invoice') or 'New'
        return super().create(vals_list)

    @api.onchange('date_from', 'date_to')
    def _onchange_date_range(self):
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise ValidationError('Ngày bắt đầu phải nhỏ hơn ngày kết thúc')
                
            # Tìm tất cả hóa đơn đã thanh toán trong khoảng thời gian
            domain = [
                ('invoice_date', '>=', self.date_from),
                ('invoice_date', '<=', self.date_to),
                ('state', '=', 'paid'),
                ('insurance_amount', '>', 0)  # Chỉ lấy hóa đơn có bảo hiểm chi trả
            ]
            invoices = self.env['clinic.invoice'].search(domain)
            
            # Xóa các chi tiết hóa đơn cũ
            self.invoice_line_ids = [(5, 0, 0)]
            
            # Tạo chi tiết hóa đơn mới
            lines = []
            for invoice in invoices:
                if invoice.insurance_amount > 0:
                    lines.append((0, 0, {
                        'invoice_id': invoice.id,
                        'patient_id': invoice.patient_id.id,
                        'invoice_date': invoice.invoice_date,
                        'service_amount': invoice.service_amount,
                        'medicine_amount': invoice.medicine_amount,
                        'insurance_amount': invoice.insurance_amount,
                    }))
            
            if not lines:
                return {
                    'warning': {
                        'title': 'Thông báo',
                        'message': 'Không tìm thấy hóa đơn nào có bảo hiểm chi trả trong khoảng thời gian này'
                    }
                }
            
            self.invoice_line_ids = lines

class ClinicInsuranceInvoiceLine(models.Model):
    _name = 'clinic.invoice.insurance.line'
    _description = 'Chi tiết hóa đơn bảo hiểm'
    
    insurance_invoice_id = fields.Many2one('clinic.invoice.insurance', string='Hóa đơn bảo hiểm')
    invoice_id = fields.Many2one('clinic.invoice', string='Hóa đơn')
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân')
    invoice_date = fields.Date(string='Ngày hóa đơn')
    service_amount = fields.Float(string='Tiền dịch vụ')
    medicine_amount = fields.Float(string='Tiền thuốc')
    insurance_amount = fields.Float(string='Số tiền bảo hiểm chi trả')

    def action_view_invoice(self):
        """Mở form xem chi tiết hóa đơn"""
        return {
            'name': 'Chi tiết hóa đơn',
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.invoice',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'new',
            'flags': {'mode': 'readonly'},  # Chỉ cho phép xem
        }