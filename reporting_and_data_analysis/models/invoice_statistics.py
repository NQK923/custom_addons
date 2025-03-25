# -*- coding: utf-8 -*-

from odoo import models, fields, tools


class InvoiceStatistics(models.Model):
    _name = 'invoice.statistics'
    _description = 'Thống kê hóa đơn'
    _auto = False
    _order = 'invoice_date desc'

    name = fields.Char(string='Mã hóa đơn')
    display_name = fields.Char(string='Số hóa đơn')
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân')
    invoice_date = fields.Date(string='Ngày hóa đơn')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái')
    service_amount = fields.Float(string='Tiền dịch vụ')
    medicine_amount = fields.Float(string='Tiền thuốc')
    amount_total = fields.Float(string='Tổng cộng')
    insurance_amount = fields.Float(string='Bảo hiểm chi trả')
    patient_amount = fields.Float(string='Bệnh nhân chi trả')

    # For grouping and analysis
    month = fields.Char(string='Tháng', readonly=True)
    year = fields.Char(string='Năm', readonly=True)
    day = fields.Char(string='Ngày', readonly=True)

    # Add fields to track service and product usage
    service_count = fields.Integer(string='Số dịch vụ')
    product_count = fields.Integer(string='Số thuốc')
    has_insurance = fields.Boolean(string='Có bảo hiểm')

    # Prescription information
    prescription_id = fields.Many2one('prescription.order', string='Đơn thuốc')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    inv.id as id,
                    inv.name as name,
                    inv.display_name as display_name,
                    inv.patient_id as patient_id,
                    inv.invoice_date as invoice_date,
                    inv.state as state,
                    inv.service_amount as service_amount,
                    inv.medicine_amount as medicine_amount,
                    inv.amount_total as amount_total,
                    inv.insurance_amount as insurance_amount,
                    inv.patient_amount as patient_amount,
                    inv.prescription_id as prescription_id,
                    TO_CHAR(inv.invoice_date, 'DD') as day,
                    TO_CHAR(inv.invoice_date, 'MM') as month,
                    TO_CHAR(inv.invoice_date, 'YYYY') as year,
                    (SELECT COUNT(*) FROM clinic_invoice_line 
                     WHERE invoice_id = inv.id AND service_id IS NOT NULL) as service_count,
                    (SELECT COUNT(*) FROM clinic_invoice_line 
                     WHERE invoice_id = inv.id AND product_id IS NOT NULL) as product_count,
                    CASE WHEN inv.insurance_amount > 0 THEN true ELSE false END as has_insurance
                FROM
                    clinic_invoice inv
            )
        ''' % self._table)