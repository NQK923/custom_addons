from odoo import http
from odoo.http import request

class PatientHistoryController(http.Controller):
    @http.route('/clinic/patient_history', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def patient_history(self, **kwargs):
        search_value = kwargs.get('search_value', '')
        patients = False
        history = False

        if search_value:
            patients = request.env['clinic.patient'].sudo().search([
                '|', ('code', 'ilike', search_value), ('name', 'ilike', search_value)
            ], limit=1)
            if patients:
                history = request.env['patient.medical.history'].sudo().search([('patient_id', '=', patients.id)], limit=1)
                if not history:
                    history = request.env['patient.medical.history'].sudo().create({'patient_id': patients.id})

        values = {
            'patients': patients,
            'history': history,
            'search_value': search_value,
        }
        return request.render('patient_medical_history.patient_history_template', values)  # Sửa tên template