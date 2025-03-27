from odoo import http
from odoo.http import request

class MedicalHistoryController(http.Controller):
    @http.route('/medical/history', type='http', auth='public', website=True)
    def medical_history(self, patient_identifier=None, **kwargs):
        if not patient_identifier:
            return request.render('patient_medical_history.patient_medical_history_website', {})

        # Khởi tạo domain tìm kiếm
        domain = []

        # Kiểm tra xem patient_identifier có phải là số (ID) hay không
        if patient_identifier.isdigit():
            domain = ['|', ('id', '=', int(patient_identifier)), ('name', 'ilike', patient_identifier)]
        else:
            # Tìm kiếm theo code hoặc name
            domain = ['|', ('code', 'ilike', patient_identifier), ('name', 'ilike', patient_identifier)]

        # Tìm bệnh nhân
        patient = request.env['clinic.patient'].sudo().search(domain, limit=1)

        if not patient:
            return request.render('patient_medical_history.patient_medical_history_website', {
                'error': 'Không tìm thấy bệnh nhân. Vui lòng kiểm tra lại mã hoặc tên.'
            })

        # Lấy lịch sử khám bệnh
        history = request.env['patient.medical.history'].sudo().get_history_by_patient(patient.id)
        return request.render('patient_medical_history.patient_medical_history_website', {
            'history': history
        })