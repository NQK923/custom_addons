# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api


class MedicalReport(models.Model):
    _name = 'hospital.medical.report'
    _description = 'Báo cáo y tế'

    name = fields.Char('Tên báo cáo', required=True)
    date_from = fields.Date('Từ ngày', required=True, default=lambda self: datetime.now().date() - timedelta(days=30))
    date_to = fields.Date('Đến ngày', required=True, default=lambda self: datetime.now().date())
    report_type = fields.Selection([
        ('patient', 'Tình hình bệnh nhân'),
        ('epidemiology', 'Dịch tễ học'),
        ('service_quality', 'Chất lượng dịch vụ'),
        ('performance', 'Chỉ số hiệu suất')
    ], string='Loại báo cáo', required=True, default='patient')

    report_data = fields.Text('Dữ liệu báo cáo', readonly=True)
    chart_image = fields.Binary('Biểu đồ', attachment=True)

    department_id = fields.Many2one('clinic.department', string='Khoa/Phòng')
    staff_id = fields.Many2one('clinic.staff', string='Người tạo báo cáo')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('generated', 'Đã tạo'),
        ('approved', 'Đã duyệt')
    ], string='Trạng thái', default='draft')

    @api.model
    def create(self, vals):
        vals[
            'name'] = f"{dict(self._fields['report_type'].selection).get(vals.get('report_type'))} - {vals.get('date_from')} đến {vals.get('date_to')}"
        return super(MedicalReport, self).create(vals)

    def generate_report(self):
        self.ensure_one()
        if self.report_type == 'patient':
            self._generate_patient_report()
        elif self.report_type == 'epidemiology':
            self._generate_epidemiology_report()
        elif self.report_type == 'service_quality':
            self._generate_service_quality_report()
        elif self.report_type == 'performance':
            self._generate_performance_report()

        self.state = 'generated'
        return True

    def _generate_patient_report(self):
        # Lấy dữ liệu từ các model liên quan
        Patient = self.env['clinic.patient']
        Appointment = self.env['clinic.appointment']

        # Tổng số bệnh nhân mới
        new_patients = Patient.search_count([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to)
        ])

        # Tổng số lượt khám
        appointments = Appointment.search_count([
            ('appointment_date', '>=', self.date_from),
            ('appointment_date', '<=', self.date_to)
        ])

        # Báo cáo theo độ tuổi (giả sử có trường date_of_birth trong model Patient)
        age_groups = {
            '0-18': 0,
            '19-40': 0,
            '41-60': 0,
            '60+': 0
        }

        patients = Patient.search([])
        for patient in patients:
            if patient.date_of_birth:
                age = datetime.now().year - patient.date_of_birth.year
                if age <= 18:
                    age_groups['0-18'] += 1
                elif age <= 40:
                    age_groups['19-40'] += 1
                elif age <= 60:
                    age_groups['41-60'] += 1
                else:
                    age_groups['60+'] += 1

        # Tạo báo cáo
        report = f"""
        BÁO CÁO TÌNH HÌNH BỆNH NHÂN
        Thời gian: {self.date_from} đến {self.date_to}

        1. Tổng quan:
        - Tổng số bệnh nhân mới: {new_patients}
        - Tổng số lượt khám: {appointments}

        2. Phân bố theo độ tuổi:
        - 0-18 tuổi: {age_groups['0-18']} bệnh nhân
        - 19-40 tuổi: {age_groups['19-40']} bệnh nhân
        - 41-60 tuổi: {age_groups['41-60']} bệnh nhân
        - Trên 60 tuổi: {age_groups['60+']} bệnh nhân
        """

        self.report_data = report
        # Ở đây có thể thêm code để tạo biểu đồ và gán vào chart_image

    def _generate_epidemiology_report(self):
        Diagnosis = self.env['medical.test']

        # Lấy số lượng chẩn đoán theo mã ICD-10
        diagnoses = Diagnosis.search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ])

        disease_stats = {}
        for diag in diagnoses:
            if diag.test_code in disease_stats:
                disease_stats[diag.test_code]['count'] += 1
            else:
                disease_stats[diag.test_code] = {
                    'name': diag.test_code,
                    'count': 1
                }

        # Sắp xếp theo số lượng giảm dần
        sorted_diseases = sorted(disease_stats.items(), key=lambda x: x[1]['count'], reverse=True)

        # Tạo báo cáo
        report = f"""
        BÁO CÁO DỊCH TỄ HỌC
        Thời gian: {self.date_from} đến {self.date_to}

        Top 10 bệnh/chẩn đoán phổ biến:
        """

        for i, (icd_code, data) in enumerate(sorted_diseases[:10], 1):
            report += f"\n{i}. {data['name']} ({icd_code}): {data['count']} ca"

        self.report_data = report

    def _generate_service_quality_report(self):
        Feedback = self.env['healthcare.patient.feedback']

        feedbacks = Feedback.search([
            ('feedback_date', '>=', self.date_from),
            ('feedback_date', '<=', self.date_to)
        ])

        # Dictionary để lưu đánh giá theo loại phản hồi
        feedback_types = {
            'compliment': {'total': 0, 'count': 0},
            'suggestion': {'total': 0, 'count': 0},
            'complaint': {'total': 0, 'count': 0},
            'question': {'total': 0, 'count': 0},
            'other': {'total': 0, 'count': 0}
        }

        department_ratings = {}

        total_satisfaction = 0
        satisfaction_count = 0

        for feedback in feedbacks:
            # Bỏ qua nếu không có đánh giá mức độ hài lòng
            if not feedback.satisfaction_rating:
                continue

            rating_value = int(feedback.satisfaction_rating)

            # Cập nhật đánh giá theo loại phản hồi
            if feedback.feedback_type:
                feedback_types[feedback.feedback_type]['total'] += rating_value
                feedback_types[feedback.feedback_type]['count'] += 1

            if feedback.department_name:
                dept_id = feedback.department_name.id
                dept_name = feedback.department_name.name
                if dept_id not in department_ratings:
                    department_ratings[dept_id] = {'name': dept_name, 'total': 0, 'count': 0}
                department_ratings[dept_id]['total'] += rating_value
                department_ratings[dept_id]['count'] += 1

            # Cập nhật đánh giá tổng thể
            total_satisfaction += rating_value
            satisfaction_count += 1

        # Tạo báo cáo
        report = f"""
        BÁO CÁO CHẤT LƯỢNG DỊCH VỤ
        Thời gian: {self.date_from} đến {self.date_to}

        Đánh giá mức độ hài lòng theo loại phản hồi (thang điểm 5):
        - Khen ngợi: {feedback_types['compliment']['total'] / feedback_types['compliment']['count'] if feedback_types['compliment']['count'] else 0:.2f}
        - Góp ý: {feedback_types['suggestion']['total'] / feedback_types['suggestion']['count'] if feedback_types['suggestion']['count'] else 0:.2f}
        - Khiếu nại: {feedback_types['complaint']['total'] / feedback_types['complaint']['count'] if feedback_types['complaint']['count'] else 0:.2f}
        - Hỏi đáp: {feedback_types['question']['total'] / feedback_types['question']['count'] if feedback_types['question']['count'] else 0:.2f}
        - Khác: {feedback_types['other']['total'] / feedback_types['other']['count'] if feedback_types['other']['count'] else 0:.2f}

        Đánh giá mức độ hài lòng theo phòng ban (thang điểm 5):
        """

        for dept_data in department_ratings.values():
            avg_rating = dept_data['total'] / dept_data['count'] if dept_data['count'] else 0
            report += f"- {dept_data['name']}: {avg_rating:.2f}\n"

        report += f"""
        Đánh giá mức độ hài lòng tổng thể: {total_satisfaction / satisfaction_count if satisfaction_count else 0:.2f}

        Tổng số phản hồi: {len(feedbacks)}
        Số phản hồi có đánh giá: {satisfaction_count}
        """

        self.report_data = report

    def _generate_performance_report(self):
        Doctor = self.env['clinic.staff']
        Appointment = self.env['clinic.appointment']

        doctors = Doctor.search([])
        doctor_stats = {}

        for doctor in doctors:
            appointments = Appointment.search([
                ('doctor_id', '=', doctor.id),
                ('appointment_date', '>=', self.date_from),
                ('appointment_date', '<=', self.date_to)
            ])

            completed = len([a for a in appointments if a.state == 'done'])
            cancelled = len([a for a in appointments if a.state == 'cancel'])

            doctor_stats[doctor.id] = {
                'name': doctor.name,
                'total': len(appointments),
                'completed': completed,
                'cancelled': cancelled,
                'completion_rate': completed / len(appointments) * 100 if len(appointments) else 0
            }

        # Tính thời gian chờ trung bình
        all_appointments = Appointment.search([
            ('appointment_date', '>=', self.date_from),
            ('appointment_date', '<=', self.date_to),
            ('actual_start_time', '!=', False),
            ('scheduled_time', '!=', False)
        ])

        total_waiting_time = sum(
            (a.actual_start_time - a.scheduled_time).total_seconds() / 60 for a in all_appointments)
        avg_waiting_time = total_waiting_time / len(all_appointments) if all_appointments else 0

        # Tạo báo cáo
        report = f"""
        BÁO CÁO CHỈ SỐ HIỆU SUẤT
        Thời gian: {self.date_from} đến {self.date_to}

        1. Hiệu suất bác sĩ:
        """

        for doctor_id, stats in doctor_stats.items():
            report += f"\n- {stats['name']}: {stats['completed']}/{stats['total']} ca ({stats['completion_rate']:.1f}%)"

        report += f"""

        2. Thời gian chờ:
        - Thời gian chờ trung bình: {avg_waiting_time:.1f} phút

        3. Tỷ lệ hoàn thành:
        - Tổng số lịch hẹn: {sum(stats['total'] for stats in doctor_stats.values())}
        - Hoàn thành: {sum(stats['completed'] for stats in doctor_stats.values())}
        - Tỷ lệ hoàn thành: {sum(stats['completed'] for stats in doctor_stats.values()) / sum(stats['total'] for stats in doctor_stats.values()) * 100 if sum(stats['total'] for stats in doctor_stats.values()) else 0:.1f}%
        """

        self.report_data = report


class MedicalReportWizard(models.TransientModel):
    _name = 'hospital.medical.report.wizard'
    _description = 'Trình tạo báo cáo y tế'

    date_from = fields.Date('Từ ngày', required=True, default=lambda self: datetime.now().date() - timedelta(days=30))
    date_to = fields.Date('Đến ngày', required=True, default=lambda self: datetime.now().date())
    report_type = fields.Selection([
        ('patient', 'Tình hình bệnh nhân'),
        ('epidemiology', 'Dịch tễ học'),
        ('service_quality', 'Chất lượng dịch vụ'),
        ('performance', 'Chỉ số hiệu suất')
    ], string='Loại báo cáo', required=True, default='patient')
    department_id = fields.Many2one('clinic.department', string='Khoa/Phòng')

    def create_report(self):
        self.ensure_one()
        report = self.env['hospital.medical.report'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
            'report_type': self.report_type,
            'department_id': self.department_id.id if self.department_id else False,
        })

        # Tạo báo cáo ngay lập tức
        report.generate_report()

        # Mở báo cáo vừa tạo
        return {
            'name': 'Báo cáo y tế',
            'view_mode': 'form',
            'res_model': 'hospital.medical.report',
            'res_id': report.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }