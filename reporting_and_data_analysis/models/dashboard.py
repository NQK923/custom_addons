from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime
import calendar


class ClinicDashboard(models.Model):
    _name = 'clinic.dashboard'
    _description = 'Bảng điều khiển phòng khám'
    _auto = False

    name = fields.Char(string='Tên')
    date = fields.Date(string='Ngày')
    month = fields.Char(string='Tháng', compute='_compute_month', store=True)
    year = fields.Char(string='Năm', compute='_compute_year', store=True)

    # Doanh thu
    total_amount = fields.Float(string='Tổng doanh thu')
    service_amount = fields.Float(string='Doanh thu dịch vụ')
    medicine_amount = fields.Float(string='Doanh thu thuốc')

    # Bảo hiểm
    insurance_amount = fields.Float(string='Bảo hiểm chi trả')
    patient_amount = fields.Float(string='Bệnh nhân chi trả')

    # Nhóm theo
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân')
    service_id = fields.Many2one('clinic.service', string='Dịch vụ')
    product_id = fields.Many2one('pharmacy.product', string='Thuốc')

    @api.depends('date')
    def _compute_month(self):
        for record in self:
            if record.date:
                record.month = record.date.strftime('%m/%Y')
            else:
                record.month = ''

    @api.depends('date')
    def _compute_year(self):
        for record in self:
            if record.date:
                record.year = record.date.strftime('%Y')
            else:
                record.year = ''

    def init(self):
        tools = self.env['ir.model.data']
        self._cr.execute("""
            CREATE OR REPLACE VIEW clinic_dashboard AS (
                SELECT
                    ROW_NUMBER() OVER() as id,
                    i.name as name,
                    i.invoice_date as date,
                    i.amount_total as total_amount,
                    i.service_amount as service_amount,
                    i.medicine_amount as medicine_amount,
                    i.insurance_amount as insurance_amount,
                    i.patient_amount as patient_amount,
                    i.patient_id as patient_id,
                    NULL as service_id,
                    NULL as product_id
                FROM
                    clinic_invoice i
                WHERE
                    i.state = 'paid'

                UNION ALL

                SELECT
                    ROW_NUMBER() OVER() + 1000000 as id,
                    CONCAT(i.name, '/', l.id) as name,
                    i.invoice_date as date,
                    l.price_subtotal as total_amount,
                    CASE WHEN l.service_id IS NOT NULL THEN l.price_subtotal ELSE 0 END as service_amount,
                    CASE WHEN l.product_id IS NOT NULL THEN l.price_subtotal ELSE 0 END as medicine_amount,
                    l.insurance_amount as insurance_amount,
                    l.patient_amount as patient_amount,
                    i.patient_id as patient_id,
                    l.service_id as service_id,
                    l.product_id as product_id
                FROM
                    clinic_invoice_line l
                JOIN
                    clinic_invoice i ON l.invoice_id = i.id
                WHERE
                    i.state = 'paid'
            )
        """)


class ClinicDashboardWizard(models.TransientModel):
    _name = 'clinic.dashboard.wizard'
    _description = 'Tùy chọn bảng điều khiển'

    date_from = fields.Date(string='Từ ngày', default=lambda self: datetime.today().replace(day=1))
    date_to = fields.Date(string='Đến ngày', default=lambda self: datetime.today().replace(
        day=calendar.monthrange(datetime.today().year, datetime.today().month)[1]))

    def action_view_dashboard(self):
        self.ensure_one()
        action = self.env.ref('clinic_dashboard.action_clinic_dashboard').read()[0]
        action['domain'] = [('date', '>=', self.date_from), ('date', '<=', self.date_to)]
        action['context'] = {'date_from': self.date_from, 'date_to': self.date_to}
        return action