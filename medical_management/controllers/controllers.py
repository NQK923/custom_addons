# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import base64
import json
from datetime import datetime


class MedicalWebsite(http.Controller):
    def _check_manager_access(self):
        """
        Kiểm tra xem người dùng hiện tại có phải là quản lý xét nghiệm y tế không
        Trả về True nếu có quyền, False nếu không
        """
        current_user = request.env.user
        is_manager = current_user.has_group('medical_management.group_medical_manager')
        return is_manager

    # Trang chủ - Hiển thị danh sách xét nghiệm
    @http.route('/medical/tests', auth='user', website=True)
    def medical_tests(self, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        tests = request.env['medical.test'].sudo().search([])
        return request.render('medical_management.medical_tests_list', {
            'tests': tests,
        })

    # Trang chi tiết xét nghiệm
    @http.route('/medical/test/<int:test_id>', auth='user', website=True)
    def medical_test_detail(self, test_id, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        test = request.env['medical.test'].sudo().browse(test_id)
        if not test.exists():
            return request.redirect('/medical/tests')

        related_images = request.env['medical.images'].sudo().search([('MedicalTest_id', '=', test_id)])
        return request.render('medical_management.medical_test_detail', {
            'test': test,
            'related_images': related_images,
        })

    # Form tạo xét nghiệm mới
    @http.route('/medical/test/create', auth='user', website=True)
    def medical_test_create_form(self, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        patients = request.env['clinic.patient'].sudo().search([])
        doctors = request.env['clinic.staff'].sudo().search([])
        test_types = dict(request.env['medical.test']._fields['test_type'].selection)
        return request.render('medical_management.medical_test_create_form', {
            'patients': patients,
            'doctors': doctors,
            'test_types': test_types,
        })

    # Lưu xét nghiệm mới
    @http.route('/medical/test/save', auth='user', website=True, type='http', methods=['POST'])
    def medical_test_save(self, **post):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        vals = {
            'test_code': post.get('test_code'),
            'patient_id': int(post.get('patient_id')),
            'doctor_id': int(post.get('doctor_id')),
            'test_type': post.get('test_type'),
            'test_date': fields.Datetime.now(),
            'status': 'request',
            'result': post.get('result', '')
        }
        new_test = request.env['medical.test'].sudo().create(vals)
        return request.redirect('/medical/test/%s' % new_test.id)

    # Trang danh sách hình ảnh
    @http.route('/medical/images', auth='user', website=True)
    def medical_images(self, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        images = request.env['medical.images'].sudo().search([])
        return request.render('medical_management.medical_images_list', {
            'images': images,
        })

    # Trang chi tiết hình ảnh
    @http.route('/medical/image/<int:image_id>', auth='user', website=True)
    def medical_image_detail(self, image_id, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        image = request.env['medical.images'].sudo().browse(image_id)
        if not image.exists():
            return request.redirect('/medical/images')

        return request.render('medical_management.medical_image_detail', {
            'image': image,
        })

    # Form tạo hình ảnh mới
    @http.route('/medical/image/create', auth='user', website=True)
    def medical_image_create_form(self, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        tests = request.env['medical.test'].sudo().search([])
        test_types = dict(request.env['medical.images']._fields['test_type_img'].selection)
        return request.render('medical_management.medical_image_create_form', {
            'tests': tests,
            'test_types': test_types,
        })

    # Lưu hình ảnh mới - Updated with fixes
    @http.route('/medical/image/save', auth='user', website=True, type='http', methods=['POST'])
    def medical_image_save(self, **post):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        image_data = False
        if post.get('image_file'):
            # Properly encode image file
            image_file = post.get('image_file')
            image_data = base64.b64encode(image_file.read())

            # Store as string for proper template rendering
            if isinstance(image_data, bytes):
                image_data = image_data.decode('utf-8')

        # Create a test_code if empty
        test_code = post.get('test_code')
        if not test_code or test_code.strip() == '':
            # Find the last record to generate a sequential code
            last_record = request.env['medical.images'].sudo().search([], order='id desc', limit=1)
            if last_record and last_record.test_code and last_record.test_code.isdigit():
                test_code = str(int(last_record.test_code) + 1)
            else:
                test_code = '1001'  # Starting code

        vals = {
            'test_code': test_code,
            'MedicalTest_id': int(post.get('MedicalTest_id')),
            'test_type_img': post.get('test_type_img'),
            'img_date': fields.Datetime.now(),
            'result_Img': post.get('result_Img', ''),
            'Img': image_data
        }

        new_image = request.env['medical.images'].sudo().create(vals)
        return request.redirect('/medical/image/%s' % new_image.id)

    # Chỉnh sửa xét nghiệm
    @http.route('/medical/test/edit/<int:test_id>', auth='user', website=True)
    def medical_test_edit(self, test_id, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        test = request.env['medical.test'].sudo().browse(test_id)
        if not test.exists():
            return request.redirect('/medical/tests')
        patients = request.env['clinic.patient'].sudo().search([])
        doctors = request.env['clinic.staff'].sudo().search([])
        test_types = dict(request.env['medical.test']._fields['test_type'].selection)
        status_types = dict(request.env['medical.test']._fields['status'].selection)
        return request.render('medical_management.medical_test_edit_form', {
            'test': test,
            'patients': patients,
            'doctors': doctors,
            'test_types': test_types,
            'status_types': status_types
        })

    # Cập nhật xét nghiệm
    @http.route('/medical/test/update', auth='user', website=True, type='http', methods=['POST'])
    def medical_test_update(self, **post):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        test_id = int(post.get('test_id'))
        test = request.env['medical.test'].sudo().browse(test_id)

        vals = {
            'test_code': post.get('test_code'),
            'patient_id': int(post.get('patient_id')),
            'doctor_id': int(post.get('doctor_id')),
            'test_type': post.get('test_type'),
            'status': post.get('status'),
            'result': post.get('result', '')
        }

        test.write(vals)
        return request.redirect('/medical/test/%s' % test_id)

    # Xóa xét nghiệm
    @http.route('/medical/test/delete/<int:test_id>', auth='user', website=True)
    def medical_test_delete(self, test_id, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        test = request.env['medical.test'].sudo().browse(test_id)
        if test.exists():
            # Kiểm tra các hình ảnh liên quan
            related_images = request.env['medical.images'].sudo().search([('MedicalTest_id', '=', test_id)])
            if related_images:
                # Xóa các hình ảnh liên quan trước
                related_images.unlink()
            # Sau đó xóa xét nghiệm
            test.unlink()
        return request.redirect('/medical/tests')

    # Chỉnh sửa hình ảnh
    @http.route('/medical/image/edit/<int:image_id>', auth='user', website=True)
    def medical_image_edit(self, image_id, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        image = request.env['medical.images'].sudo().browse(image_id)
        if not image.exists():
            return request.redirect('/medical/images')

        tests = request.env['medical.test'].sudo().search([])
        test_types = dict(request.env['medical.images']._fields['test_type_img'].selection)

        return request.render('medical_management.medical_image_edit_form', {
            'image': image,
            'tests': tests,
            'test_types': test_types
        })

    # Cập nhật hình ảnh
    @http.route('/medical/image/update', auth='user', website=True, type='http', methods=['POST'])
    def medical_image_update(self, **post):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        image_id = int(post.get('image_id'))
        image = request.env['medical.images'].sudo().browse(image_id)

        vals = {
            'test_code': post.get('test_code'),
            'MedicalTest_id': int(post.get('MedicalTest_id')),
            'test_type_img': post.get('test_type_img'),
            'result_Img': post.get('result_Img', '')
        }

        # Chỉ cập nhật hình ảnh nếu có file mới được tải lên
        if post.get('image_file'):
            image_file = post.get('image_file')
            image_data = base64.b64encode(image_file.read())

            if isinstance(image_data, bytes):
                image_data = image_data.decode('utf-8')

            vals['Img'] = image_data

        image.write(vals)
        return request.redirect('/medical/image/%s' % image_id)

    # Xóa hình ảnh
    @http.route('/medical/image/delete/<int:image_id>', auth='user', website=True)
    def medical_image_delete(self, image_id, **kw):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        image = request.env['medical.images'].sudo().browse(image_id)
        if image.exists():
            test_id = image.MedicalTest_id.id
            image.unlink()
            # Quay về trang chi tiết xét nghiệm nếu có
            if test_id:
                return request.redirect('/medical/test/%s' % test_id)
        return request.redirect('/medical/images')

    # Cập nhật nhanh trạng thái xét nghiệm (AJAX)
    @http.route('/medical/test/update_status', auth='user', website=True, type='http', methods=['POST'], csrf=False)
    def medical_test_update_status(self, **post):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return json.dumps({'success': False, 'error': 'Không có quyền truy cập'})

        if not post.get('test_id') or not post.get('status'):
            return json.dumps({'success': False, 'error': 'Missing parameters'})

        try:
            test_id = int(post.get('test_id'))
            test = request.env['medical.test'].sudo().browse(test_id)

            if not test.exists():
                return json.dumps({'success': False, 'error': 'Test not found'})

            test.write({'status': post.get('status')})
            return json.dumps({'success': True})
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})