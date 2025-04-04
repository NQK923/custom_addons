from odoo import http
from odoo.http import request
import werkzeug
from datetime import date


class PatientController(http.Controller):
    @http.route('/patients', type='http', auth='user', website=True)
    def patient_list(self, **kw):
        # Xử lý tham số tìm kiếm và bộ lọc
        search = kw.get('search', '')
        patient_type = kw.get('patient_type', '')
        gender = kw.get('gender', '')
        sort = kw.get('sort', 'date desc')  # Mặc định sắp xếp theo ngày giảm dần

        # Xây dựng domain
        domain = []
        if search:
            domain += ['|', '|',
                       ('code', 'ilike', search),
                       ('name', 'ilike', search),
                       ('phone', 'ilike', search)]
        if patient_type:
            domain += [('patient_type', '=', patient_type)]
        if gender:
            domain += [('gender', '=', gender)]

        # Xác định thứ tự sắp xếp
        order = 'date desc'  # Mặc định
        if sort == 'code':
            order = 'code'
        elif sort == 'name':
            order = 'name'
        elif sort == 'age':
            order = 'age desc'
        elif sort == 'date':
            order = 'date desc'

        # Phân trang
        page = int(kw.get('page', 1))
        limit = 10
        offset = (page - 1) * limit

        # Lấy tổng số bản ghi để tính phân trang
        total_count = request.env['clinic.patient'].search_count(domain)
        pager = self._get_pager(page, limit, total_count, '/patients', kw)

        # Lấy danh sách bệnh nhân theo bộ lọc
        patients = request.env['clinic.patient'].search(domain, limit=limit, offset=offset, order=order)

        # Trả về template với dữ liệu
        return request.render('patient_management.patient_list_template', {
            'patients': patients,
            'pager': pager,
            'search_count': total_count,
            'search': search,
            'patient_type': patient_type,
            'gender': gender,
            'sort': sort,
        })

    def _get_pager(self, page, limit, total, url, url_args=None):
        """Hàm helper để tạo đối tượng phân trang."""
        if url_args is None:
            url_args = {}

        # Tính toán các thông số phân trang
        page_count = int(total / limit) + (1 if total % limit else 0)
        if page_count <= 1:
            return None

        url_args = dict(url_args)  # Tạo bản sao để tránh thay đổi đối tượng gốc

        # Tạo URL cho các trang
        def get_page_url(page):
            url_args['page'] = page
            return '%s?%s' % (url, werkzeug.urls.url_encode(url_args))

        # Tạo thông tin cho các trang
        pages = []
        for p in range(1, page_count + 1):
            pages.append({
                'num': p,
                'url': get_page_url(p),
                'active': p == page
            })

        return {
            'page_count': page_count,
            'offset': (page - 1) * limit,
            'page': page,
            'page_start': max(page - 2, 1),
            'page_previous': {'num': page - 1, 'url': get_page_url(page - 1)} if page > 1 else None,
            'page_next': {'num': page + 1, 'url': get_page_url(page + 1)} if page < page_count else None,
            'page_end': min(page + 2, page_count),
            'page_ids': pages,
        }

    @http.route('/patients/<model("clinic.patient"):patient>', type='http', auth='user', website=True)
    def patient_detail(self, patient, **kw):
        # Hiển thị thông báo thành công nếu có
        message = kw.get('message', '')
        message_type = kw.get('message_type', '')

        # Lấy chi tiết bệnh nhân
        return request.render('patient_management.patient_form_template', {
            'patient': patient,
            'today': date.today(),
            'message': message,
            'message_type': message_type,
        })

    @http.route('/patients/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def patient_create(self, **kw):
        # Xử lý tạo mới bệnh nhân
        if request.httprequest.method == 'POST':
            try:
                # Xử lý dữ liệu form
                vals = {
                    'name': kw.get('name'),
                    'email': kw.get('email'),
                    'phone': kw.get('phone'),
                    'gender': kw.get('gender'),
                    'date_of_birth': kw.get('date_of_birth') or False,  # False nếu là chuỗi rỗng
                    'patient_type': kw.get('patient_type', 'outpatient'),
                    'note': kw.get('note'),
                }

                # Tạo bệnh nhân mới
                new_patient = request.env['clinic.patient'].create(vals)

                # Chuyển hướng đến trang chi tiết bệnh nhân với thông báo thành công
                return werkzeug.utils.redirect(
                    f'/patients/{new_patient.id}?message=Đã tạo bệnh nhân mới thành công&message_type=success')
            except Exception as e:
                # Trả về form với thông báo lỗi
                return request.render('patient_management.patient_create_template', {
                    'error_message': f"Lỗi: {str(e)}",
                    'values': kw,
                    'genders': [('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')],
                    'patient_types': [('outpatient', 'Ngoại trú'), ('inpatient', 'Nội trú')],
                })

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
            try:
                # Xử lý dữ liệu form
                vals = {
                    'name': kw.get('name'),
                    'email': kw.get('email'),
                    'phone': kw.get('phone'),
                    'gender': kw.get('gender'),
                    'date_of_birth': kw.get('date_of_birth') or False,  # False nếu là chuỗi rỗng
                    'note': kw.get('note'),
                }

                # Cập nhật thông tin bệnh nhân
                patient.write(vals)

                # Chuyển hướng đến trang chi tiết bệnh nhân với thông báo thành công
                return werkzeug.utils.redirect(
                    f'/patients/{patient.id}?message=Đã cập nhật thông tin bệnh nhân thành công&message_type=success')
            except Exception as e:
                # Trả về form với thông báo lỗi
                return request.render('patient_management.patient_edit_template', {
                    'error_message': f"Lỗi: {str(e)}",
                    'patient': patient,
                    'genders': [('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')],
                })

        # Trả về template form cập nhật
        return request.render('patient_management.patient_edit_template', {
            'patient': patient,
            'genders': [('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')],
        })