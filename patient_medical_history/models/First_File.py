from odoo import models, fields, api

class PatientMedicalHistory(models.Model):
    _name = 'patient.medical.history'
    _description = 'Patient Medical History'

    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True)
    history_date = fields.Datetime(string='Ngày ghi nhận', default=fields.Datetime.now)
    medical_tests = fields.One2many('medical.test', 'patient_id', string='Xét nghiệm', readonly=True)
    medical_images = fields.One2many('medical.images', compute='_compute_medical_images', string='Hình ảnh y tế', readonly=True)
    treatment_plans = fields.One2many('treatment.plan', 'patient_id', string='Kế hoạch điều trị', readonly=True)
    treatment_processes = fields.One2many('treatment.process', compute='_compute_treatment_processes', string='Quá trình điều trị', readonly=True)

    @api.depends('patient_id')
    def _compute_medical_images(self):
        for record in self:
            tests = record.medical_tests.mapped('id')
            record.medical_images = self.env['medical.images'].search([('MedicalTest_id', 'in', tests)])

    @api.depends('patient_id')
    def _compute_treatment_processes(self):
        for record in self:
            plans = record.treatment_plans.mapped('id')
            record.treatment_processes = self.env['treatment.process'].search([('plan_id', 'in', plans)])

    def get_history_by_patient(self, patient_id):
        """Lấy lịch sử khám bệnh dựa trên patient_id."""
        history = self.search([('patient_id', '=', patient_id)], limit=1)
        if history:
            history._compute_medical_images()
            history._compute_treatment_processes()
        return history