from odoo import models, fields, api


class MedicalTest(models.Model):
    _name = 'medical.test'
    _description = 'Medical Test Management'

    test_code = fields.Char(string='Mã xét nghiệm và chuẩn đoán', required=True)
    patient_id = fields.Many2one('clinic.patient', string='Bệnh nhân', required=True)  # Tham chiếu module khác
    doctor_id = fields.Many2one(
        'clinic.staff',
        string='Người thực hiện',
        required=True
    )
    test_type = fields.Selection([
        ('test', 'Chuẩn đoán'),
        ('blood', 'Máu'),
        ('urine', 'Nước tiểu'),
        ('xray', 'X-Quang'),
        ('ecg', 'ECG'),
        ('other', 'Khác')
    ], string='Loại xét nghiệm hoặc chuẩn đoán', required=True)
    test_date = fields.Datetime(string='Ngày thực hiện', required=True)
    status = fields.Selection([
        ('request', 'Yêu cầu'),
        ('processing', 'Đang xử lý'),
        ('completed', 'Hoàn tất')
    ], string='Trạng thái', default='request')
    result = fields.Text(string='Kết quả xét nghiệm hoặc chuẩn đoán')


class MedicalImages(models.Model):
    _name = 'medical.images'
    _description = 'Images'

    test_code = fields.Char(
        string='Mã Hình ảnh xét nghiệm',
        required=True,
        copy=False,
    )
    MedicalTest_id = fields.Many2one('medical.test', string='Mã xét nghiệm', required=True)
    test_type_img = fields.Selection([
        ('test', 'Chuẩn đoán'),
        ('blood', 'Máu'),
        ('urine', 'Nước tiểu'),
        ('xray', 'X-Quang'),
        ('ecg', 'ECG'),
        ('other', 'Khác')
    ], string='Loại xét nghiệm hoặc chuẩn đoán', required=True)
    img_date = fields.Datetime(string='Ngày thực hiện', required=True)
    result_Img = fields.Text(string='Kết quả Chuẩn đoán hoặc chuẩn đoán')

    # Updated field definition with proper attachment settings
    Img = fields.Binary(string='Prescription Image', attachment=True)

    # Method to ensure test_code is always populated
    @api.model
    def create(self, vals):
        # Check if test_code is provided
        if not vals.get('test_code') or vals.get('test_code').strip() == '':
            # Auto-generate code based on existing records
            last_record = self.search([], order='id desc', limit=1)
            next_code = 1001  # Default starting number

            if last_record and last_record.test_code:
                try:
                    next_code = int(last_record.test_code) + 1
                except (ValueError, TypeError):
                    # If conversion fails, use default
                    pass

            vals['test_code'] = str(next_code)

        return super(MedicalImages, self).create(vals)