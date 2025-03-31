from odoo import http
from odoo.http import request
import werkzeug
from datetime import date


class PatientController(http.Controller):
    @http.route('/patients', type='http', auth='user', website=True)
    def patient_list(self, **kw):
        # Lấy danh sách bệnh nhân
        patients = request.env['clinic.patient'].search([])
        return request.render('patient_management.patient_list_template', {
            'patients': patients,
        })

    @http.route('/patients/<model("clinic.patient"):patient>', type='http', auth='user', website=True)
    def patient_detail(self, patient, **kw):
        # Lấy chi tiết bệnh nhân
        return request.render('patient_management.patient_form_template', {
            'patient': patient,
            'today': date.today(),
        })

    @http.route('/patients/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def patient_create(self, **kw):
        # Xử lý tạo mới bệnh nhân
        if request.httprequest.method == 'POST':
            # Xử lý dữ liệu form
            vals = {
                'name': kw.get('name'),
                'email': kw.get('email'),
                'phone': kw.get('phone'),
                'gender': kw.get('gender'),
                'date_of_birth': kw.get('date_of_birth'),
                'patient_type': kw.get('patient_type', 'outpatient'),
                'note': kw.get('note'),
            }

            # Tạo bệnh nhân mới
            new_patient = request.env['clinic.patient'].create(vals)

            # Chuyển hướng đến trang chi tiết bệnh nhân
            return werkzeug.utils.redirect(f'/patients/{new_patient.id}')

        # Trả về template form tạo mới
        return request.render('patient_management.patient_create_template', {
            'genders': [('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')],
            'patient_types': [('outpatient', 'Ngoại trú'), ('inpatient', 'Nội trú')],
        })

    @http.route('/patients/<model("clinic.patient"):patient>/edit', type='http', auth='user', website=True,
                methods=['GET', 'POST'])
    def patient_edit(self, patient, **kw):
        # Xử lý cập nhật thông tin bệnh nhân
        if request.httprequest.method == 'POST':
            # Xử lý dữ liệu form
            vals = {
                'name': kw.get('name'),
                'email': kw.get('email'),
                'phone': kw.get('phone'),
                'gender': kw.get('gender'),
                'date_of_birth': kw.get('date_of_birth'),
                'note': kw.get('note'),
            }

            # Cập nhật thông tin bệnh nhân
            patient.write(vals)

            # Chuyển hướng đến trang chi tiết bệnh nhân
            return werkzeug.utils.redirect(f'/patients/{patient.id}')

        # Trả về template form cập nhật
        return request.render('patient_management.patient_edit_template', {
            'patient': patient,
            'genders': [('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')],
        })