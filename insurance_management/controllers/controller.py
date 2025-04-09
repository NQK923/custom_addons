from odoo import http
from odoo.http import request
from datetime import date


class InsuranceController(http.Controller):
    @http.route('/clinic/insurance', type='http', auth='public', website=True, methods=['GET'])
    def insurance_list(self, **kwargs):
        """Hiển thị danh sách các bảo hiểm y tế"""
        insurance_policies = request.env['clinic.insurance.policy'].sudo().search([])
        values = {
            'insurance_policies': insurance_policies,
        }
        return request.render('insurance_management.insurance_list_template', values)

    @http.route('/clinic/insurance/<model("clinic.insurance.policy"):insurance>', type='http', auth='public',
                website=True, methods=['GET'])
    def insurance_detail(self, insurance, **kwargs):
        """Hiển thị chi tiết thông tin bảo hiểm y tế"""
        values = {
            'insurance': insurance,
        }
        return request.render('insurance_management.insurance_detail_template', values)

    @http.route('/clinic/insurance/create', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def insurance_create(self, **kwargs):
        """Tạo mới thông tin bảo hiểm y tế"""
        # Lấy danh sách bệnh nhân để hiển thị dropdown
        patients = request.env['clinic.patient'].sudo().search([])

        error = {}
        if request.httprequest.method == 'POST':
            patient_id = int(kwargs.get('patient_id', 0))
            number = kwargs.get('number', '')
            facility = kwargs.get('facility', '')
            expiry_date = kwargs.get('expiry_date', '')
            coverage_rate = kwargs.get('coverage_rate', '')

            # Kiểm tra dữ liệu nhập vào
            if not patient_id:
                error['patient_id'] = 'Vui lòng chọn bệnh nhân'
            if not number:
                error['number'] = 'Vui lòng nhập số thẻ BHYT'
            if not facility:
                error['facility'] = 'Vui lòng nhập nơi ĐKKCB'
            if not expiry_date:
                error['expiry_date'] = 'Vui lòng nhập ngày hết hạn'
            if not coverage_rate:
                error['coverage_rate'] = 'Vui lòng chọn mức chi trả'

            if patient_id and not error.get('patient_id'):
                existing_insurance = request.env['clinic.insurance.policy'].sudo().search([
                    ('patient_id', '=', patient_id)
                ], limit=1)

                if existing_insurance:
                    error['patient_id'] = 'Bệnh nhân này đã có bảo hiểm y tế!'
            if not error:
                try:
                    insurance = request.env['clinic.insurance.policy'].sudo().create({
                        'patient_id': patient_id,
                        'number': number,
                        'facility': facility,
                        'expiry_date': expiry_date,
                        'coverage_rate': coverage_rate,
                        'name': 'New',  # Sẽ được tự động tạo trong model
                    })
                    return request.redirect('/clinic/insurance/%s' % insurance.id)
                except Exception as e:
                    error['general'] = str(e)

        values = {
            'patients': patients,
            'error': error,
            'kwargs': kwargs,
        }
        return request.render('insurance_management.insurance_form_template', values)

    @http.route('/clinic/insurance/<model("clinic.insurance.policy"):insurance>/edit', type='http', auth='public',
                website=True, methods=['GET', 'POST'])
    def insurance_edit(self, insurance, **kwargs):
        """Chỉnh sửa thông tin bảo hiểm y tế"""
        # Lấy danh sách bệnh nhân để hiển thị dropdown
        patients = request.env['clinic.patient'].sudo().search([])

        error = {}
        if request.httprequest.method == 'POST':
            # Lấy dữ liệu từ form
            patient_id = int(kwargs.get('patient_id', 0))
            number = kwargs.get('number', '')
            facility = kwargs.get('facility', '')
            expiry_date = kwargs.get('expiry_date', '')
            coverage_rate = kwargs.get('coverage_rate', '')

            # Kiểm tra dữ liệu nhập vào
            if not patient_id:
                error['patient_id'] = 'Vui lòng chọn bệnh nhân'
            if not number:
                error['number'] = 'Vui lòng nhập số thẻ BHYT'
            if not facility:
                error['facility'] = 'Vui lòng nhập nơi ĐKKCB'
            if not expiry_date:
                error['expiry_date'] = 'Vui lòng nhập ngày hết hạn'
            if not coverage_rate:
                error['coverage_rate'] = 'Vui lòng chọn mức chi trả'

            if patient_id and patient_id != insurance.patient_id.id and not error.get('patient_id'):
                existing_insurance = request.env['clinic.insurance.policy'].sudo().search([
                    ('patient_id', '=', patient_id),
                    ('id', '!=', insurance.id)
                ], limit=1)

                if existing_insurance:
                    error['patient_id'] = 'Bệnh nhân này đã có bảo hiểm y tế!'

            # Nếu dữ liệu hợp lệ, cập nhật bản ghi
            if not error:
                try:
                    insurance.sudo().write({
                        'patient_id': patient_id,
                        'number': number,
                        'facility': facility,
                        'expiry_date': expiry_date,
                        'coverage_rate': coverage_rate,
                    })
                    return request.redirect('/clinic/insurance/%s' % insurance.id)
                except Exception as e:
                    error['general'] = str(e)

        values = {
            'insurance': insurance,
            'patients': patients,
            'error': error,
            'kwargs': kwargs,
        }
        return request.render('insurance_management.insurance_form_template', values)

    @http.route('/clinic/insurance/<model("clinic.insurance.policy"):insurance>/delete', type='http', auth='public',
                website=True, methods=['POST'])
    def insurance_delete(self, insurance, **kwargs):
        """Xóa thông tin bảo hiểm y tế"""
        try:
            insurance.sudo().unlink()
            return request.redirect('/clinic/insurance')
        except Exception as e:
            values = {
                'insurance': insurance,
                'error': str(e),
            }
            return request.render('insurance_management.insurance_detail_template', values)