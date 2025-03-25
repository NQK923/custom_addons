from odoo import models, fields, api, tools
from psycopg2.extensions import AsIs
from datetime import datetime, timedelta


class InvoiceReportMonthly(models.Model):
    _name = 'clinic.invoice.report.monthly'
    _description = 'Phân tích hóa đơn theo tháng'
    _auto = False
    _order = 'year desc, month desc'

    name = fields.Char(string='Kỳ', readonly=True)
    year = fields.Integer(string='Năm', readonly=True)
    month = fields.Integer(string='Tháng', readonly=True)
    month_name = fields.Char(string='Tên tháng', readonly=True)
    date = fields.Date(string='Ngày', readonly=True)

    invoice_count = fields.Integer(string='Số hóa đơn', readonly=True)
    service_amount = fields.Float(string='Doanh thu dịch vụ', readonly=True)
    medicine_amount = fields.Float(string='Doanh thu thuốc', readonly=True)
    total_amount = fields.Float(string='Tổng doanh thu', readonly=True)
    insurance_amount = fields.Float(string='Bảo hiểm chi trả', readonly=True)
    patient_amount = fields.Float(string='Bệnh nhân chi trả', readonly=True)

    avg_service_amount = fields.Float(string='Doanh thu dịch vụ TB', readonly=True, group_operator='avg')
    avg_medicine_amount = fields.Float(string='Doanh thu thuốc TB', readonly=True, group_operator='avg')
    avg_total_amount = fields.Float(string='Tổng doanh thu TB', readonly=True, group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = '''
            CREATE OR REPLACE VIEW %(table)s AS (
                SELECT
                    row_number() OVER () as id,
                    to_char(invoice_date, 'YYYY-MM') AS name,
                    EXTRACT(year FROM invoice_date) AS year,
                    EXTRACT(month FROM invoice_date) AS month,
                    to_char(invoice_date, 'Month') AS month_name,
                    DATE_TRUNC('month', invoice_date) AS date,
                    COUNT(id) AS invoice_count,
                    SUM(service_amount) AS service_amount,
                    SUM(medicine_amount) AS medicine_amount,
                    SUM(amount_total) AS total_amount,
                    SUM(insurance_amount) AS insurance_amount,
                    SUM(patient_amount) AS patient_amount,
                    AVG(service_amount) AS avg_service_amount,
                    AVG(medicine_amount) AS avg_medicine_amount,
                    AVG(amount_total) AS avg_total_amount
                FROM
                    clinic_invoice
                WHERE
                    state IN ('confirmed', 'paid')
                GROUP BY
                    to_char(invoice_date, 'YYYY-MM'),
                    EXTRACT(year FROM invoice_date),
                    EXTRACT(month FROM invoice_date),
                    to_char(invoice_date, 'Month'),
                    DATE_TRUNC('month', invoice_date)
                ORDER BY
                    year DESC, month DESC
            )
        '''
        self._cr.execute(query, {'table': AsIs(self._table)})


class InvoiceReportService(models.Model):
    _name = 'clinic.invoice.report.service'
    _description = 'Phân tích doanh thu dịch vụ'
    _auto = False
    _order = 'total_revenue desc'

    service_id = fields.Many2one('clinic.service', string='Dịch vụ', readonly=True)
    service_name = fields.Char(string='Tên dịch vụ', readonly=True)
    total_quantity = fields.Float(string='Tổng số lượng', readonly=True)
    total_revenue = fields.Float(string='Tổng doanh thu', readonly=True)
    insurance_covered = fields.Float(string='Bảo hiểm chi trả', readonly=True)
    patient_paid = fields.Float(string='Bệnh nhân chi trả', readonly=True)
    invoice_count = fields.Integer(string='Số hóa đơn', readonly=True)
    avg_price = fields.Float(string='Giá trung bình', readonly=True, group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = '''
            CREATE OR REPLACE VIEW %(table)s AS (
                SELECT
                    MIN(l.id) as id,
                    l.service_id,
                    s.service_name,
                    SUM(l.quantity) as total_quantity,
                    SUM(l.price_subtotal) as total_revenue,
                    SUM(l.insurance_amount) as insurance_covered,
                    SUM(l.patient_amount) as patient_paid,
                    COUNT(DISTINCT l.invoice_id) as invoice_count,
                    AVG(l.price_unit) as avg_price
                FROM
                    clinic_invoice_line l
                JOIN
                    clinic_invoice i ON l.invoice_id = i.id
                LEFT JOIN
                    clinic_service s ON l.service_id = s.id
                WHERE
                    i.state IN ('confirmed', 'paid')
                    AND l.service_id IS NOT NULL
                GROUP BY
                    l.service_id, s.service_name
                ORDER BY
                    total_revenue DESC
            )
        '''
        self._cr.execute(query, {'table': AsIs(self._table)})


class InvoiceReportProduct(models.Model):
    _name = 'clinic.invoice.report.product'
    _description = 'Phân tích doanh thu thuốc'
    _auto = False
    _order = 'total_revenue desc'

    product_id = fields.Many2one('pharmacy.product', string='Thuốc', readonly=True)
    product_name = fields.Char(string='Tên thuốc', readonly=True)
    total_quantity = fields.Float(string='Tổng số lượng', readonly=True)
    total_revenue = fields.Float(string='Tổng doanh thu', readonly=True)
    insurance_covered = fields.Float(string='Bảo hiểm chi trả', readonly=True)
    patient_paid = fields.Float(string='Bệnh nhân chi trả', readonly=True)
    invoice_count = fields.Integer(string='Số hóa đơn', readonly=True)
    avg_price = fields.Float(string='Giá trung bình', readonly=True, group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = '''
            CREATE OR REPLACE VIEW %(table)s AS (
                SELECT
                    MIN(l.id) as id,
                    l.product_id,
                    p.name as product_name,
                    SUM(l.quantity) as total_quantity,
                    SUM(l.price_subtotal) as total_revenue,
                    SUM(l.insurance_amount) as insurance_covered,
                    SUM(l.patient_amount) as patient_paid,
                    COUNT(DISTINCT l.invoice_id) as invoice_count,
                    AVG(l.price_unit) as avg_price
                FROM
                    clinic_invoice_line l
                JOIN
                    clinic_invoice i ON l.invoice_id = i.id
                LEFT JOIN
                    pharmacy_product p ON l.product_id = p.id
                WHERE
                    i.state IN ('confirmed', 'paid')
                    AND l.product_id IS NOT NULL
                GROUP BY
                    l.product_id, p.name
                ORDER BY
                    total_revenue DESC
            )
        '''
        self._cr.execute(query, {'table': AsIs(self._table)})


class InvoiceReportPatient(models.Model):
    _name = 'clinic.invoice.report.patient'
    _description = 'Phân tích theo bệnh nhân'
    _auto = False
    _order = 'total_amount desc'

    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', readonly=True)
    patient_name = fields.Char(string='Tên bệnh nhân', readonly=True)
    has_insurance = fields.Boolean(string='Có bảo hiểm', readonly=True)
    insurance_state = fields.Char(string='Trạng thái BH', readonly=True)

    invoice_count = fields.Integer(string='Số hóa đơn', readonly=True)
    service_amount = fields.Float(string='Tiền dịch vụ', readonly=True)
    medicine_amount = fields.Float(string='Tiền thuốc', readonly=True)
    total_amount = fields.Float(string='Tổng tiền', readonly=True)
    insurance_amount = fields.Float(string='Bảo hiểm chi trả', readonly=True)
    patient_amount = fields.Float(string='Bệnh nhân chi trả', readonly=True)
    insurance_rate = fields.Float(string='Tỉ lệ BH chi trả %', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = '''
            CREATE OR REPLACE VIEW %(table)s AS (
                SELECT
                    MIN(i.id) as id,
                    i.patient_id,
                    p.name as patient_name,
                    p.has_insurance,
                    p.insurance_state,
                    COUNT(i.id) as invoice_count,
                    SUM(i.service_amount) as service_amount,
                    SUM(i.medicine_amount) as medicine_amount,
                    SUM(i.amount_total) as total_amount,
                    SUM(i.insurance_amount) as insurance_amount,
                    SUM(i.patient_amount) as patient_amount,
                    CASE WHEN SUM(i.amount_total) > 0 
                        THEN (SUM(i.insurance_amount) / SUM(i.amount_total)) * 100
                        ELSE 0
                    END as insurance_rate
                FROM
                    clinic_invoice i
                JOIN
                    clinic_patient p ON i.patient_id = p.id
                WHERE
                    i.state IN ('confirmed', 'paid')
                GROUP BY
                    i.patient_id, p.name, p.has_insurance, p.insurance_state
                ORDER BY
                    total_amount DESC
            )
        '''
        self._cr.execute(query, {'table': AsIs(self._table)})


class InvoiceReportStatus(models.Model):
    _name = 'clinic.invoice.report.status'
    _description = 'Phân tích trạng thái hóa đơn'
    _auto = False
    _order = 'year desc, month desc, state'

    name = fields.Char(string='Kỳ', readonly=True)
    year = fields.Integer(string='Năm', readonly=True)
    month = fields.Integer(string='Tháng', readonly=True)
    month_name = fields.Char(string='Tên tháng', readonly=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', readonly=True)

    invoice_count = fields.Integer(string='Số hóa đơn', readonly=True)
    total_amount = fields.Float(string='Tổng tiền', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = '''
            CREATE OR REPLACE VIEW %(table)s AS (
                SELECT
                    row_number() OVER () as id,
                    to_char(invoice_date, 'YYYY-MM') || '-' || state AS name,
                    EXTRACT(year FROM invoice_date) AS year,
                    EXTRACT(month FROM invoice_date) AS month,
                    to_char(invoice_date, 'Month') AS month_name,
                    state,
                    COUNT(id) AS invoice_count,
                    SUM(amount_total) AS total_amount
                FROM
                    clinic_invoice
                GROUP BY
                    to_char(invoice_date, 'YYYY-MM'),
                    EXTRACT(year FROM invoice_date),
                    EXTRACT(month FROM invoice_date),
                    to_char(invoice_date, 'Month'),
                    state
                ORDER BY
                    year DESC, month DESC, state
            )
        '''
        self._cr.execute(query, {'table': AsIs(self._table)})