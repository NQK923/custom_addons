from odoo import http
from odoo.http import request


class PrescriptionManagementController(http.Controller):
    @http.route('/pharmacy/prescriptions', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def prescription_list(self, **kwargs):
        search_value = kwargs.get('search_value', '')
        prescriptions = False
        patient = False

        if search_value:
            # Search for patient by code or name
            patient = request.env['clinic.patient'].sudo().search([
                '|', ('code', 'ilike', search_value), ('name', 'ilike', search_value)
            ], limit=1)

            if patient:
                # Get prescriptions for this patient
                prescriptions = request.env['prescription.order'].sudo().search([
                    ('patient_id', '=', patient.id)
                ], order='date desc')

        values = {
            'patient': patient,
            'prescriptions': prescriptions,
            'search_value': search_value,
        }
        return request.render('prescription_management.prescription_list_template', values)

    @http.route('/pharmacy/prescription/<model("prescription.order"):prescription_id>', type='http', auth='public',
                website=True)
    def prescription_detail(self, prescription_id, **kwargs):
        if not prescription_id:
            return request.redirect('/pharmacy/prescriptions')

        values = {
            'prescription': prescription_id,
            'prescription_lines': prescription_id.prescription_line_ids,
        }
        return request.render('prescription_management.prescription_detail_template', values)