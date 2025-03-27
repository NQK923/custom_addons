from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import uuid  # Add this at the top

class ClinicService(models.Model):
    _name = 'clinic.service'
    _description = 'Dịch vụ phòng khám'
    _rec_name = 'service_name'

    name = fields.Char(string='Mã dịch vụ', required=True, copy=False, readonly=True, default='New')
    service_name = fields.Char(string='Tên dịch vụ', required=True)
    price = fields.Float(string='Giá dịch vụ', required=True)
    description = fields.Text(string='Mô tả')
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

class ClinicInvoice(models.Model):
    _name = 'clinic.invoice'
    _description = 'Hóa đơn phòng khám'
    _order = 'invoice_date desc, id desc'
    _rec_name = 'display_name'  # Add this

    name = fields.Char(string='Mã hóa đơn', required=True, copy=False, readonly=True, default='New')
    display_name = fields.Char(string='Số hóa đơn', compute='_compute_display_name', store=True)
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True)
    prescription_ids = fields.Many2many('prescription.order', string='Đơn thuốc',
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

    # Thêm trường treatment_plan_id
    treatment_plan_id = fields.Many2one('treatment.plan', string='Kế hoạch điều trị',
                                      domain="[('patient_id', '=', patient_id)]")

    @api.depends('name', 'invoice_date')
    def _compute_display_name(self):
        for record in self:
            if record.invoice_date:
                record.display_name = f'HD{record.invoice_date.strftime("%Y%m%d")}-{record.name}'
            else:
                record.display_name = record.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

    @api.depends('service_lines.price_subtotal', 'product_lines.price_subtotal', 'patient_id')
    def _compute_amounts(self):
        for invoice in self:
            # Tính tổng tiền dịch vụ và thuốc
            invoice.service_amount = sum(line.price_subtotal for line in invoice.service_lines)
            invoice.medicine_amount = sum(line.price_subtotal for line in invoice.product_lines)
            invoice.amount_total = invoice.service_amount + invoice.medicine_amount
            
            # Kiểm tra bảo hiểm hợp lệ
            has_valid_insurance = False
            if invoice.patient_id and invoice.patient_id.has_insurance:
                if invoice.patient_id.insurance_state == 'Hợp lệ':
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
        self.prescription_ids = [(5, 0, 0)]  # Clear prescriptions
        self.treatment_plan_id = False  # Clear treatment plan
        self.service_lines = [(5, 0, 0)]  # Clear service lines
        self.product_lines = [(5, 0, 0)]  # Clear product lines

    @api.onchange('prescription_ids')
    def _onchange_prescription_ids(self):
        """Handle multiple prescriptions"""
        if self.prescription_ids:
            # Clear existing product lines first
            self.product_lines = [(5, 0, 0)]
            new_lines = []
            
            for prescription in self.prescription_ids:
                for line in prescription.prescription_line_ids:
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
                        
                    # Kiểm tra xem thuốc đã tồn tại trong lines chưa
                    existing_line = next((l for l in new_lines if l[2]['product_id'] == product.id), None)
                    if existing_line:
                        # Nếu đã tồn tại, cộng thêm số lượng
                        existing_line[2]['quantity'] += line.quantity
                    else:
                        # Nếu chưa tồn tại, thêm line mới
                        new_lines.append((0, 0, {
                            'product_id': product.id,
                            'quantity': line.quantity,
                            'price_unit': product.unit_price,
                        }))
                
            self.product_lines = new_lines

    @api.onchange('treatment_plan_id')
    def _onchange_treatment_plan(self):
        """Load services from treatment plan"""
        if self.treatment_plan_id:
            # Clear existing service lines first
            self.service_lines = [(5, 0, 0)]
            new_lines = []
            
            # Add services from treatment processes
            for process in self.treatment_plan_id.treatment_process_ids:
                service = process.service_id
                if not service:
                    continue
                    
                if not service.price:
                    raise ValidationError(
                        f"Dịch vụ '{service.service_name}' chưa có giá. Vui lòng thiết lập giá trước khi sử dụng."
                    )
                new_lines.append((0, 0, {
                    'service_id': service.id,
                    'quantity': 1,
                    'price_unit': service.price,
                }))
                
            self.service_lines = new_lines

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_mark_as_paid(self):
        for invoice in self:
            # Kiểm tra số lượng tồn kho trước khi thanh toán
            for line in invoice.product_lines:
                if line.product_id.quantity < line.quantity:
                    raise ValidationError(
                        f'Không đủ số lượng thuốc {line.product_id.name} trong kho! '
                        f'(Còn {line.product_id.quantity}, cần {line.quantity})'
                    )
            
            # Cập nhật trạng thái và trừ số lượng trong kho
            invoice.write({'state': 'paid'})
            
            # Trừ số lượng thuốc trong kho
            for line in invoice.product_lines:
                line.product_id.quantity -= line.quantity

    def action_cancel(self):
        for invoice in self:
            # Nếu hóa đơn đã thanh toán, cộng lại số lượng thuốc vào kho
            if invoice.state == 'paid':
                for line in invoice.product_lines:
                    line.product_id.quantity += line.quantity
            
            invoice.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        for invoice in self:
            # Chỉ cho phép đặt lại về nháp nếu chưa thanh toán
            if invoice.state == 'paid':
                raise ValidationError(
                    'Không thể đặt lại hóa đơn đã thanh toán về trạng thái nháp!'
                )
            invoice.write({'state': 'draft'})

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
                    f"Dịch vụ '{self.service_id.service_name}' chưa có giá. Vui lòng thiết lập giá trước khi sử dụng."
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
            if line.invoice_id.patient_id and line.invoice_id.patient_id.has_insurance:
                if line.invoice_id.patient_id.insurance_state == 'Hợp lệ':
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
                    f"Đơn giá của {line.service_id.service_name or line.product_id.name} phải lớn hơn 0!"
                )
                
class ClinicInsuranceInvoice(models.Model):
    _name = 'clinic.invoice.insurance'
    _description = 'Hóa đơn bảo hiểm'
    _rec_name = 'display_name'  # Add this

    name = fields.Char(string='Mã hóa đơn BH', required=True, copy=False, readonly=True, default='New')
    display_name = fields.Char(string='Số hóa đơn BH', compute='_compute_display_name', store=True)
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

    @api.depends('name', 'date_from')
    def _compute_display_name(self):
        for record in self:
            if record.date_from:
                record.display_name = f'BHYT{record.date_from.strftime("%Y%m")}-{record.name}'
            else:
                record.display_name = record.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = str(uuid.uuid4())[:8]
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

class ClinicPurchaseOrder(models.Model):
    _name = 'clinic.purchase.order'
    _description = 'Phiếu nhập hàng'
    _rec_name = 'display_name'  # Change from 'code'

    name = fields.Char(string='Mã phiếu nhập', readonly=True, default='New')  # Renamed from 'code'
    display_name = fields.Char(string='Số phiếu nhập', compute='_compute_display_name', store=True)
    date = fields.Date(string='Ngày nhập', default=fields.Date.today, required=True)
    supplier_name = fields.Char(string='Nhà cung cấp', required=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
    ], string='Trạng thái', default='draft', tracking=True)
    
    line_ids = fields.One2many('clinic.purchase.order.line', 'order_id', string='Chi tiết phiếu nhập')
    note = fields.Text(string='Ghi chú')
    
    amount_untaxed = fields.Float(string='Tổng tiền chưa thuế', compute='_compute_amounts', store=True)
    amount_tax = fields.Float(string='Thuế (10%)', compute='_compute_amounts', store=True)
    amount_total = fields.Float(string='Tổng tiền sau thuế', compute='_compute_amounts', store=True)

    def unlink(self):
        """Chỉ cho phép xóa ở trạng thái nháp và đã xác nhận"""
        for record in self:
            if record.state == 'paid':
                raise ValidationError('Không thể xóa phiếu nhập đã thanh toán!')
        return super(ClinicPurchaseOrder, self).unlink()

    def action_confirm(self):
        """Xác nhận phiếu nhập"""
        for record in self:
            if record.state == 'draft':
                record.write({'state': 'confirmed'})

    def action_pay(self):
        """Thanh toán phiếu nhập"""
        for record in self:
            if record.state == 'confirmed':
                record.write({'state': 'paid'})
                # Cập nhật số lượng trong kho
                for line in record.line_ids:
                    line.product_id.write({
                        'quantity': line.product_id.quantity + line.quantity
                    })

    @api.depends('name', 'date')
    def _compute_display_name(self):
        for record in self:
            if record.date:
                record.display_name = f'PNH{record.date.strftime("%Y%m%d")}-{record.name}'
            else:
                record.display_name = record.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = str(uuid.uuid4())[:8]
        return super().create(vals_list)

    def write(self, vals):
        """Kiểm tra quyền chỉnh sửa"""
        for record in self:
            if record.state == 'paid' and not self.env.context.get('allow_paid_edit'):
                raise ValidationError('Không thể chỉnh sửa phiếu nhập đã thanh toán!')
        return super(ClinicPurchaseOrder, self).write(vals)

    @api.depends('line_ids.subtotal')
    def _compute_amounts(self):
        for order in self:
            amount_untaxed = sum(order.line_ids.mapped('subtotal'))
            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_untaxed * 0.1
            order.amount_total = order.amount_untaxed + order.amount_tax

class PurchaseOrderLine(models.Model):
    _name = 'clinic.purchase.order.line'
    _description = 'Chi tiết phiếu nhập'

    order_id = fields.Many2one('clinic.purchase.order', string='Phiếu nhập', required=True, ondelete='cascade')
    product_id = fields.Many2one('pharmacy.product', string='Dược phẩm', required=True)
    quantity = fields.Integer(string='Số lượng', required=True)
    price_unit = fields.Float(string='Đơn giá', required=True)
    subtotal = fields.Float(string='Thành tiền', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.purchase_price