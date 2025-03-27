from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class MedicalHistoryController(http.Controller):
    @http.route('/medical/history', type='http', auth='public', website=True)
    def medical_history(self, patient_identifier=None, **kwargs):
        if not patient_identifier:
            return request.render('patient_medical_history.patient_medical_history_website', {})

        domain = ['|', ('id', '=', int(patient_identifier)) if patient_identifier.isdigit() else ('name', 'ilike', patient_identifier), ('name', 'ilike', patient_identifier)]
        _logger.info(f"Searching patient with domain: {domain}")

        patient = request.env['clinic.patient'].sudo().search(domain, limit=1)
        _logger.info(f"Found patient: {patient.id if patient else 'None'} - {patient.name if patient else 'None'}")

        if not patient:
            return request.render('patient_medical_history.patient_medical_history_website', {
                'error': 'Không tìm thấy bệnh nhân. Vui lòng kiểm tra lại mã hoặc tên.'
            })

        history = request.env['patient.medical.history'].sudo().search([('patient_id', '=', patient.id)], limit=1)
        _logger.info(f"Found history: {history.id if history else 'None'}")

        if not history:
            return request.render('patient_medical_history.patient_medical_history_website', {
                'error': 'Không tìm thấy lịch sử khám bệnh cho bệnh nhân này.'
            })

        history._compute_medical_images()
        history._compute_treatment_processes()

        return request.render('patient_medical_history.patient_medical_history_website', {
            'history': history
        })