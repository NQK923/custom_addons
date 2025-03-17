from odoo import models, fields, api

# Kế hoạch điều trị
class TreatmentPlan(models.Model):
    _name = 'treatment.plan'
    _description = 'Treatment Plan'

    code = fields.Char(
        string='Mã kế hoạch điều trị',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    patient_id = fields.Many2one(
        'clinic.patient',
        string='Mã bệnh nhân',
        required=True
    )
    start_date = fields.Date(string='Ngày bắt đầu', required=True)
    end_date = fields.Date(string='Ngày kết thúc')
    treatment_process_ids = fields.One2many(
        'treatment.process',
        'plan_id',
        string='Quá trình điều trị'
    )

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('treatment.plan') or '1'
        return super(TreatmentPlan, self).create(vals)


from odoo.exceptions import ValidationError

class TreatmentProcess(models.Model):
    _name = 'treatment.process'
    _description = 'Treatment Process'

    code = fields.Char(
        string='Mã quá trình',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    plan_id = fields.Many2one(
        'treatment.plan',
        string='Kế hoạch điều trị',
        required=True,
        ondelete='cascade'
    )
    executor_id = fields.Many2one(
        'clinic.staff',
        string='Người thực hiện',
        required=True
    )
    state = fields.Selection([
        ('pending', 'Chưa thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành')
    ], string='Trạng thái', default='pending', required=True)
    execution_time = fields.Datetime(string='Thời gian thực hiện')
    prescription_id = fields.Many2one(
        'prescription.order',
        string='Mã đơn thuốc'
    )

    @api.model
    def create(self, vals):
        if not vals.get('executor_id'):
            raise ValidationError("Người thực hiện không được để trống.")
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('treatment.process') or '1'
        return super(TreatmentProcess, self).create(vals)

    def write(self, vals):
        if 'executor_id' in vals and not vals['executor_id']:
            raise ValidationError("Người thực hiện không được để trống.")
        return super(TreatmentProcess, self).write(vals)
