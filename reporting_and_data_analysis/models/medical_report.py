# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import base64
import io

from odoo import models, fields, api

try:
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    MATPLOTLIB_ENABLED = True
except ImportError:
    MATPLOTLIB_ENABLED = False


class MedicalReport(models.Model):
    _name = 'hospital.medical.report'
    _description = 'Báo cáo y tế'

    name = fields.Char('Tên báo cáo', required=True)
    date_from = fields.Date('Từ ngày', required=True, default=lambda self: datetime.now().date() - timedelta(days=30))
    date_to = fields.Date('Đến ngày', required=True, default=lambda self: datetime.now().date())
    report_type = fields.Selection([
        ('patient', 'Tình hình bệnh nhân'),
        ('epidemiology', 'Dịch tễ học'),
        ('service_quality', 'Chất lượng dịch vụ')
    ], string='Loại báo cáo', required=True, default='patient')

    report_data = fields.Text('Dữ liệu báo cáo', readonly=True)
    chart_image = fields.Binary('Biểu đồ', attachment=True)
    chart_filename = fields.Char('Tên file biểu đồ', default='chart.png')
    additional_chart1 = fields.Binary('Biểu đồ bổ sung 1', attachment=True)
    additional_chart1_filename = fields.Char('Tên file biểu đồ 1', default='chart1.png')
    additional_chart2 = fields.Binary('Biểu đồ bổ sung 2', attachment=True)
    additional_chart2_filename = fields.Char('Tên file biểu đồ 2', default='chart2.png')

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

        self.state = 'generated'
        return True

    def action_approve(self):
        self.ensure_one()
        self.state = 'approved'
        return True

    def action_export_pdf(self):
        """Export medical report as PDF with error handling"""
        self.ensure_one()

        if self.state == 'draft':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thông báo',
                    'message': 'Báo cáo chưa được tạo nên không thể xuất PDF.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        try:
            # Direct PDF export URL
            return {
                'type': 'ir.actions.act_url',
                'url': f'/report/medical_pdf/{self.id}',
                'target': 'new',
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Không thể xuất báo cáo PDF. Vui lòng thử lại sau.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
    def _create_chart_image(self, plt_figure):
        """Convert matplotlib figure to binary data for storing in Odoo"""
        if not MATPLOTLIB_ENABLED:
            return False

        buf = io.BytesIO()
        plt_figure.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_data = base64.b64encode(buf.getvalue())
        buf.close()
        plt.close(plt_figure)
        return img_data

    def _generate_patient_report(self):
        Patient = self.env['clinic.patient']
        Appointment = self.env['clinic.appointment']

        new_patients = Patient.search_count([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to)
        ])

        appointments = Appointment.search_count([
            ('appointment_date', '>=', self.date_from),
            ('appointment_date', '<=', self.date_to)
        ])

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

        if MATPLOTLIB_ENABLED:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

            labels = age_groups.keys()
            sizes = age_groups.values()
            explode = (0.1, 0, 0, 0)

            ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            ax1.axis('equal')
            ax1.set_title('Phân bố bệnh nhân theo độ tuổi')

            labels = ['Bệnh nhân mới', 'Lượt khám']
            values = [new_patients, appointments]

            ax2.bar(labels, values, color=['blue', 'orange'])
            ax2.set_title('Số lượng bệnh nhân mới và lượt khám')
            ax2.set_ylabel('Số lượng')

            for i, v in enumerate(values):
                ax2.text(i, v + 0.1, str(v), ha='center')

            fig.tight_layout()

            self.chart_image = self._create_chart_image(fig)

    def _generate_epidemiology_report(self):
        Diagnosis = self.env['medical.test']

        diagnoses = Diagnosis.search([
            ('test_date', '>=', self.date_from),
            ('test_date', '<=', self.date_to)
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

        sorted_diseases = sorted(disease_stats.items(), key=lambda x: x[1]['count'], reverse=True)

        report = f"""
        BÁO CÁO DỊCH TỄ HỌC
        Thời gian: {self.date_from} đến {self.date_to}

        Bệnh chẩn đoán phổ biến:
        """

        for i, (icd_code, data) in enumerate(sorted_diseases[:10], 1):
            report += f"\n{i}. {data['name']} ({icd_code}): {data['count']} ca"

        self.report_data = report

        if MATPLOTLIB_ENABLED and sorted_diseases:
            top_diseases = sorted_diseases[:min(10, len(sorted_diseases))]

            fig, ax = plt.subplots(figsize=(10, 6))

            disease_names = [f"{data['name']} ({code})" for code, data in top_diseases]
            disease_counts = [data['count'] for _, data in top_diseases]

            bars = ax.barh(disease_names, disease_counts, color='skyblue')

            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height() / 2,
                        f'{width:.0f}', ha='left', va='center')

            ax.set_xlabel('Số lượng ca')
            ax.set_title('Top bệnh/chẩn đoán phổ biến')
            fig.tight_layout()

            self.chart_image = self._create_chart_image(fig)

    def _generate_service_quality_report(self):
        Feedback = self.env['healthcare.patient.feedback']

        feedbacks = Feedback.search([
            ('feedback_date', '>=', self.date_from),
            ('feedback_date', '<=', self.date_to)
        ])

        feedback_types = {
            'compliment': {'total': 0, 'count': 0, 'name': 'Khen ngợi'},
            'suggestion': {'total': 0, 'count': 0, 'name': 'Góp ý'},
            'complaint': {'total': 0, 'count': 0, 'name': 'Khiếu nại'},
            'question': {'total': 0, 'count': 0, 'name': 'Hỏi đáp'},
            'other': {'total': 0, 'count': 0, 'name': 'Khác'}
        }

        department_ratings = {}

        total_satisfaction = 0
        satisfaction_count = 0

        for feedback in feedbacks:
            if not feedback.satisfaction_rating:
                continue

            rating_value = int(feedback.satisfaction_rating)

            if feedback.feedback_type:
                feedback_types[feedback.feedback_type]['total'] += rating_value
                feedback_types[feedback.feedback_type]['count'] += 1

            if feedback.department_id:
                dept_id = feedback.department_id.id
                dept_name = feedback.department_id.department_name
                if dept_id not in department_ratings:
                    department_ratings[dept_id] = {'name': dept_name, 'total': 0, 'count': 0}
                department_ratings[dept_id]['total'] += rating_value
                department_ratings[dept_id]['count'] += 1

            total_satisfaction += rating_value
            satisfaction_count += 1

        for fb_type in feedback_types.values():
            fb_type['avg'] = fb_type['total'] / fb_type['count'] if fb_type['count'] else 0

        for dept in department_ratings.values():
            dept['avg'] = dept['total'] / dept['count'] if dept['count'] else 0

        report = f"""
        BÁO CÁO CHẤT LƯỢNG DỊCH VỤ
        Thời gian: {self.date_from} đến {self.date_to}

        Đánh giá mức độ hài lòng theo loại phản hồi (thang điểm 5):
        - Khen ngợi: {feedback_types['compliment']['avg']:.2f}
        - Góp ý: {feedback_types['suggestion']['avg']:.2f}
        - Khiếu nại: {feedback_types['complaint']['avg']:.2f}
        - Hỏi đáp: {feedback_types['question']['avg']:.2f}
        - Khác: {feedback_types['other']['avg']:.2f}

        Đánh giá mức độ hài lòng theo phòng ban (thang điểm 5):
        """

        for dept_data in department_ratings.values():
            report += f"- {dept_data['name']}: {dept_data['avg']:.2f}\n"

        report += f"""
        Đánh giá mức độ hài lòng tổng thể: {total_satisfaction / satisfaction_count if satisfaction_count else 0:.2f}

        Tổng số phản hồi: {len(feedbacks)}
        Số phản hồi có đánh giá: {satisfaction_count}
        """

        self.report_data = report

        if MATPLOTLIB_ENABLED:
            fig1, ax1 = plt.subplots(figsize=(10, 6))

            valid_fb_types = {k: v for k, v in feedback_types.items() if v['count'] > 0}

            if valid_fb_types:
                labels = [v['name'] for v in valid_fb_types.values()]
                values = [v['avg'] for v in valid_fb_types.values()]
                counts = [v['count'] for v in valid_fb_types.values()]

                colors = ['#ff9999' if v < 3 else '#99ff99' if v > 4 else '#ffcc99' for v in values]

                bars = ax1.bar(labels, values, color=colors)

                for i, (bar, count) in enumerate(zip(bars, counts)):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                             f'{height:.2f}\n({count})', ha='center', va='bottom')

                ax1.set_ylim(0, 5.5)  # Set y-axis to accommodate the rating scale
                ax1.set_ylabel('Đánh giá trung bình')
                ax1.set_title('Đánh giá theo loại phản hồi')
                fig1.tight_layout()

                self.chart_image = self._create_chart_image(fig1)

            if department_ratings:
                fig2, ax2 = plt.subplots(figsize=(10, 6))

                dept_names = [d['name'] for d in department_ratings.values()]
                dept_avgs = [d['avg'] for d in department_ratings.values()]
                dept_counts = [d['count'] for d in department_ratings.values()]

                bars = ax2.barh(dept_names, dept_avgs, color='lightblue')

                for i, (bar, count) in enumerate(zip(bars, dept_counts)):
                    width = bar.get_width()
                    ax2.text(width + 0.1, bar.get_y() + bar.get_height() / 2.,
                             f'{width:.2f}\n({count})', ha='left', va='center')

                ax2.set_xlim(0, 5.5)
                ax2.set_xlabel('Đánh giá trung bình')
                ax2.set_title('Đánh giá theo phòng ban')
                fig2.tight_layout()

                self.additional_chart1 = self._create_chart_image(fig2)


class MedicalReportWizard(models.TransientModel):
    _name = 'hospital.medical.report.wizard'
    _description = 'Trình tạo báo cáo y tế'

    date_from = fields.Date('Từ ngày', required=True, default=lambda self: datetime.now().date() - timedelta(days=30))
    date_to = fields.Date('Đến ngày', required=True, default=lambda self: datetime.now().date())
    report_type = fields.Selection([
        ('patient', 'Tình hình bệnh nhân'),
        ('epidemiology', 'Dịch tễ học'),
        ('service_quality', 'Chất lượng dịch vụ')
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

        report.generate_report()

        return {
            'name': 'Báo cáo y tế',
            'view_mode': 'form',
            'res_model': 'hospital.medical.report',
            'res_id': report.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }