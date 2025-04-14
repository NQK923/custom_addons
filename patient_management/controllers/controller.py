from odoo import http
from odoo.http import request
import werkzeug
from datetime import date
import re
from odoo.exceptions import ValidationError
import psycopg2


class PatientController(http.Controller):
    def _check_manager_access(self):
        """
        Kiểm tra xem người dùng hiện tại có phải là quản lý bệnh nhân không
        Trả về True nếu có quyền, False nếu không
        """
        current_user = request.env.user
        is_manager = current_user.has_group('patient_management.group_patient_manager')
        return is_manager

    @http.route('/patients', type='http', auth='user', website=True)
    def patient_list(self, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        # Xử lý tham số tìm kiếm và bộ lọc
        search = kw.get('search', '')
        patient_type = kw.get('patient_type', '')
        gender = kw.get('gender', '')
        sort = kw.get('sort', 'date desc')  # Mặc định sắp xếp theo ngày giảm dần

        # Xử lý thông báo nếu có
        message = kw.get('message', '')
        message_type = kw.get('message_type', '')

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
            'message': message,
            'message_type': message_type,
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
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

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

    def _check_unique_email(self, email, patient_id=None):
        """Kiểm tra tính duy nhất của email"""
        if not email:
            return True

        email_normalized = email.strip().lower()

        domain = [('email', '!=', False)]
        if patient_id:
            domain.append(('id', '!=', patient_id))

        patients = request.env['clinic.patient'].search(domain)
        for patient in patients:
            if patient.email and patient.email.strip().lower() == email_normalized:
                return False

        return True

    def _check_unique_phone(self, phone, patient_id=None):
        """Kiểm tra tính duy nhất của số điện thoại"""
        if not phone:
            return True

        # Chuẩn hóa số điện thoại (loại bỏ các ký tự không phải số)
        phone_normalized = re.sub(r'\D', '', phone)

        # Thay vì tìm kiếm theo phone_normalized, lấy tất cả bệnh nhân có số điện thoại
        domain = [('phone', '!=', False)]
        if patient_id:
            domain.append(('id', '!=', patient_id))

        patients = request.env['clinic.patient'].search(domain)

        for patient in patients:
            if patient.phone:
                current_phone_normalized = re.sub(r'\D', '', patient.phone)
                if current_phone_normalized == phone_normalized:
                    return False

        return True

    @http.route('/patients/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def patient_create(self, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        # Xử lý tạo mới bệnh nhân
        if request.httprequest.method == 'POST':
            try:
                # Kiểm tra tính duy nhất của email và số điện thoại
                email = kw.get('email')
                phone = kw.get('phone')

                # Kiểm tra email
                if email and not self._check_unique_email(email):
                    error_msg = f"Email '{email}' đã được sử dụng!"
                    raise ValidationError(error_msg)

                # Kiểm tra số điện thoại
                if phone and not self._check_unique_phone(phone):
                    error_msg = f"Số điện thoại '{phone}' đã được sử dụng!"
                    raise ValidationError(error_msg)

                # Xử lý dữ liệu form
                vals = {
                    'name': kw.get('name'),
                    'email': email,
                    'phone': phone,
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
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        # Xử lý cập nhật thông tin bệnh nhân
        if request.httprequest.method == 'POST':
            try:
                # Kiểm tra tính duy nhất của email và số điện thoại
                email = kw.get('email')
                phone = kw.get('phone')

                # Kiểm tra email
                if email and not self._check_unique_email(email, patient.id):
                    error_msg = f"Email '{email}' đã được sử dụng!"
                    raise ValidationError(error_msg)

                # Kiểm tra số điện thoại
                if phone and not self._check_unique_phone(phone, patient.id):
                    error_msg = f"Số điện thoại '{phone}' đã được sử dụng!"
                    raise ValidationError(error_msg)

                # Xử lý dữ liệu form
                vals = {
                    'name': kw.get('name'),
                    'email': email,
                    'phone': phone,
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

    @http.route('/patients/<model("clinic.patient"):patient>/delete', type='http', auth='user', website=True,
                methods=['POST'])
    def patient_delete(self, patient, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        try:
            # Lấy tên của bệnh nhân để hiển thị trong thông báo
            patient_name = patient.name

            # Xóa bệnh nhân
            patient.unlink()

            # Chuyển hướng đến danh sách bệnh nhân với thông báo thành công
            return werkzeug.utils.redirect(
                f'/patients?message=Đã xóa bệnh nhân {patient_name} thành công&message_type=success')
        except Exception as e:
            error_message = str(e)
            redirect_url = f'/patients/{patient.id}'

            # Kiểm tra nếu là lỗi ràng buộc khóa ngoại
            if "violates foreign key constraint" in error_message:
                # Xác định loại ràng buộc từ thông báo lỗi
                if "clinic_insurance_policy" in error_message:
                    friendly_message = f"Không thể xóa bệnh nhân '{patient.name}' vì bệnh nhân đang có thông tin bảo hiểm y tế. Vui lòng xóa thông tin bảo hiểm trước khi xóa bệnh nhân."
                else:
                    friendly_message = f"Không thể xóa bệnh nhân '{patient.name}' vì bệnh nhân đang có thông tin liên quan trong hệ thống. Vui lòng xóa các thông tin liên quan trước khi xóa bệnh nhân."

                return werkzeug.utils.redirect(
                    f'{redirect_url}?message={friendly_message}&message_type=error')

            # Các lỗi khác
            return werkzeug.utils.redirect(
                f'{redirect_url}?message=Lỗi khi xóa bệnh nhân: {error_message}&message_type=error')