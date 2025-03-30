# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import base64
import json
from datetime import datetime


class MedicalWebsite(http.Controller):
    # Trang chủ - Hiển thị danh sách xét nghiệm
    @http.route('/medical/tests', auth='user', website=True)
    def medical_tests(self, **kw):
        tests = request.env['medical.test'].sudo().search([])
        return request.render('medical_management.medical_tests_list', {
            'tests': tests,
        })

    # Trang chi tiết xét nghiệm
    @http.route('/medical/test/<int:test_id>', auth='user', website=True)
    def medical_test_detail(self, test_id, **kw):
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
        images = request.env['medical.images'].sudo().search([])
        return request.render('medical_management.medical_images_list', {
            'images': images,
        })

    # Trang chi tiết hình ảnh
    @http.route('/medical/image/<int:image_id>', auth='user', website=True)
    def medical_image_detail(self, image_id, **kw):
        image = request.env['medical.images'].sudo().browse(image_id)
        if not image.exists():
            return request.redirect('/medical/images')

        return request.render('medical_management.medical_image_detail', {
            'image': image,
        })

    # Form tạo hình ảnh mới
    @http.route('/medical/image/create', auth='user', website=True)
    def medical_image_create_form(self, **kw):
        tests = request.env['medical.test'].sudo().search([])
        test_types = dict(request.env['medical.images']._fields['test_type_img'].selection)
        return request.render('medical_management.medical_image_create_form', {
            'tests': tests,
            'test_types': test_types,
        })

    # Lưu hình ảnh mới - Updated with fixes
    @http.route('/medical/image/save', auth='user', website=True, type='http', methods=['POST'])
    def medical_image_save(self, **post):
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