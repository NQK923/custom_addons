# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

from odoo import http
from odoo.http import request, content_disposition

_logger = logging.getLogger(__name__)


def _return_error_response(message):
    """Return a simple error response"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Error</title></head>
    <body>
        <h1>Error</h1>
        <p>{message}</p>
        <p>Please contact your administrator.</p>
    </body>
    </html>
    """
    return request.make_response(html, headers=[('Content-Type', 'text/html')])


class MedicalReportPDFController(http.Controller):
    def _check_manager_access(self):
        """
        Kiểm tra xem người dùng hiện tại có phải là quản lý báo cáo không
        Trả về True nếu có quyền, False nếu không
        """
        current_user = request.env.user
        is_manager = current_user.has_group('reporting_and_data_analysis.group_reporting_manager')
        return is_manager

    @http.route(['/report/medical_pdf/<int:report_id>'], type='http', auth="user")
    def get_medical_report_pdf(self, report_id, **kwargs):
        """Generate PDF report for medical reports using ReportLab"""
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        try:
            # Check if the report model exists
            report_model_name = 'report.med_report_pdf'
            if report_model_name not in request.env:
                _logger.error(f"Report model {report_model_name} not found")
                return _return_error_response("Report model not found in the system")

            # Get the report handler model
            report_model = request.env[report_model_name]

            # Get the medical report record
            medical_report = request.env['hospital.medical.report'].browse(report_id)

            if not medical_report.exists():
                return request.not_found()

            # Generate PDF using the report handler
            pdf_content = report_model._get_pdf(medical_report)

            if not pdf_content:
                return _return_error_response("Failed to generate PDF content")

            # Set the appropriate headers for a PDF download
            filename = f"medical_report_{report_id}.pdf"
            headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', content_disposition(filename))
            ]

            # Return the PDF as a response
            return request.make_response(pdf_content, headers=headers)

        except Exception as e:
            _logger.error(f"Error generating medical report PDF: {e}")
            return _return_error_response(f"Error generating PDF: {e}")


def _get_monthly_data(year=None):
    domain = []
    if year:
        domain = [('year', '=', year)]

    try:
        monthly_reports = request.env['clinic.invoice.report.monthly'].search(domain, order='year desc, month')
        return monthly_reports.read([
            'name', 'year', 'month', 'month_name', 'invoice_count',
            'service_amount', 'medicine_amount', 'total_amount',
            'insurance_amount', 'patient_amount'
        ])
    except Exception as e:
        _logger.error(f"Error getting monthly data: {e}")
        return []


def _get_service_data():
    try:
        service_reports = request.env['clinic.invoice.report.service'].search([], order='total_revenue desc')
        return service_reports.read([
            'service_name', 'total_quantity', 'total_revenue',
            'insurance_covered', 'patient_paid', 'invoice_count', 'avg_price'
        ])
    except Exception as e:
        _logger.error(f"Error getting service data: {e}")
        return []


def _get_product_data():
    try:
        product_reports = request.env['clinic.invoice.report.product'].search([], order='total_revenue desc')
        return product_reports.read([
            'product_name', 'total_quantity', 'total_revenue',
            'insurance_covered', 'patient_paid', 'invoice_count', 'avg_price'
        ])
    except Exception as e:
        _logger.error(f"Error getting product data: {e}")
        return []


def _get_patient_data():
    try:
        patient_reports = request.env['clinic.invoice.report.patient'].search([], order='total_amount desc')
        return patient_reports.read([
            'patient_name', 'invoice_count', 'service_amount', 'medicine_amount',
            'total_amount', 'insurance_amount', 'patient_amount', 'insurance_rate'
        ])
    except Exception as e:
        _logger.error(f"Error getting patient data: {e}")
        return []


def _get_status_data(year=None):
    domain = []
    if year:
        domain = [('year', '=', year)]

    try:
        status_reports = request.env['clinic.invoice.report.status'].search(domain, order='year desc, month, state')
        return status_reports.read([
            'name', 'year', 'month', 'month_name', 'state', 'invoice_count', 'total_amount'
        ])
    except Exception as e:
        _logger.error(f"Error getting status data: {e}")
        return []


class WebsiteReportController(http.Controller):
    def _check_manager_access(self):
        """
        Kiểm tra xem người dùng hiện tại có phải là quản lý báo cáo không
        Trả về True nếu có quyền, False nếu không
        """
        current_user = request.env.user
        is_manager = current_user.has_group('reporting_and_data_analysis.group_reporting_manager')
        return is_manager

    # Define formatLang helper method - UPDATED to use simple Python formatting
    def formatLang(self, value, digits=None, grouping=True, monetary=False, dp=False, currency_obj=False):
        """Helper method to correctly format amounts for templates"""
        try:
            # Định dạng số đơn giản
            if digits is not None:
                return f"{float(value):,.{digits}f}"
            elif isinstance(value, float):
                return f"{value:,.2f}"
            else:
                return f"{value:,}"
        except Exception as e:
            _logger.error(f"Error in formatLang: {e}")
            return str(value)

    # Dashboard route
    @http.route('/clinic/reports/dashboard', type='http', auth='user', website=True)
    def reports_dashboard(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        # Prepare dashboard data
        monthly_data = _get_monthly_data()  # Gọi hàm toàn cục, không phải self._get_monthly_data()
        service_data = _get_service_data()  # Gọi hàm toàn cục, không phải self._get_service_data()
        product_data = _get_product_data()  # Gọi hàm toàn cục, không phải self._get_product_data()

        values = {
            'monthly_data': monthly_data,
            'service_data': service_data,
            'product_data': product_data,
            'page_name': 'dashboard',  # Đảm bảo tham số này được đặt để tab Tổng Quan active
            'formatLang': self.formatLang,
            'json': json,
        }
        return request.render('reporting_and_data_analysis.reports_dashboard_template', values)

    # Invoice report routes
    @http.route('/clinic/reports/invoice/monthly', type='http', auth='user', website=True)
    def invoice_monthly(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        year = int(kwargs.get('year', datetime.now().year))
        # Get monthly reports for selected year
        monthly_data = _get_monthly_data(year=year)

        # Prepare data for charts
        months = [data['month_name'] for data in monthly_data if data['year'] == year]
        service_amounts = [data['service_amount'] for data in monthly_data if data['year'] == year]
        medicine_amounts = [data['medicine_amount'] for data in monthly_data if data['year'] == year]
        total_amounts = [data['total_amount'] for data in monthly_data if data['year'] == year]

        chart_data = {
            'months': json.dumps(months),
            'service_amounts': json.dumps(service_amounts),
            'medicine_amounts': json.dumps(medicine_amounts),
            'total_amounts': json.dumps(total_amounts),
        }

        values = {
            'monthly_data': monthly_data,
            'chart_data': chart_data,
            'selected_year': year,
            'years': range(datetime.now().year - 5, datetime.now().year + 1),
            'page_name': 'invoice_monthly',
            'formatLang': self.formatLang,
        }
        return request.render('reporting_and_data_analysis.invoice_monthly_template', values)

    @http.route('/clinic/reports/invoice/services', type='http', auth='user', website=True)
    def invoice_services(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        service_data = _get_service_data()

        # Prepare data for charts
        services = [data['service_name'] for data in service_data[:10]]  # Top 10 services
        revenues = [data['total_revenue'] for data in service_data[:10]]

        chart_data = {
            'services': json.dumps(services),
            'revenues': json.dumps(revenues),
        }

        values = {
            'service_data': service_data,
            'chart_data': chart_data,
            'page_name': 'invoice_services',
            'formatLang': self.formatLang,
        }
        return request.render('reporting_and_data_analysis.invoice_services_template', values)

    @http.route('/clinic/reports/invoice/products', type='http', auth='user', website=True)
    def invoice_products(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        product_data = _get_product_data()

        # Prepare data for charts
        products = [data['product_name'] for data in product_data[:10]]  # Top 10 products
        revenues = [data['total_revenue'] for data in product_data[:10]]

        chart_data = {
            'products': json.dumps(products),
            'revenues': json.dumps(revenues),
        }

        values = {
            'product_data': product_data,
            'chart_data': chart_data,
            'page_name': 'invoice_products',
            'formatLang': self.formatLang,
        }
        return request.render('reporting_and_data_analysis.invoice_products_template', values)

    @http.route('/clinic/reports/invoice/patients', type='http', auth='user', website=True)
    def invoice_patients(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        patient_data = _get_patient_data()

        values = {
            'patient_data': patient_data,
            'page_name': 'invoice_patients',
            'formatLang': self.formatLang,
        }
        return request.render('reporting_and_data_analysis.invoice_patients_template', values)

    @http.route('/clinic/reports/invoice/status', type='http', auth='user', website=True)
    def invoice_status(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        year = int(kwargs.get('year', datetime.now().year))
        status_data = _get_status_data(year=year)

        values = {
            'status_data': status_data,
            'selected_year': year,
            'years': range(datetime.now().year - 5, datetime.now().year + 1),
            'page_name': 'invoice_status',
            'formatLang': self.formatLang,
        }
        return request.render('reporting_and_data_analysis.invoice_status_template', values)

    # Medical report routes
    @http.route('/clinic/reports/medical', type='http', auth='user', website=True)
    def medical_reports_list(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        reports = request.env['hospital.medical.report'].search([])

        values = {
            'reports': reports,
            'page_name': 'medical_reports',
        }
        return request.render('reporting_and_data_analysis.medical_reports_list_template', values)

    @http.route('/clinic/reports/medical/<int:report_id>', type='http', auth='user', website=True)
    def medical_report_detail(self, report_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        report = request.env['hospital.medical.report'].browse(report_id)
        if not report.exists():
            return request.redirect('/clinic/reports/medical')

        values = {
            'report': report,
            'page_name': 'medical_report_detail',
        }
        return request.render('reporting_and_data_analysis.medical_report_detail_template', values)

    @http.route('/clinic/reports/medical/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def medical_report_create(self, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        if request.httprequest.method == 'POST':
            # Create new report
            try:
                report_type = kwargs.get('report_type')
                date_from = kwargs.get('date_from')
                date_to = kwargs.get('date_to')
                department_id = int(kwargs.get('department_id')) if kwargs.get('department_id') else False
                staff_id = int(kwargs.get('staff_id')) if kwargs.get('staff_id') else False

                # Create report values
                report_vals = {
                    'report_type': report_type,
                    'date_from': date_from,
                    'date_to': date_to,
                    'department_id': department_id,
                    'staff_id': staff_id,  # Sử dụng staff_id từ form thay vì tự động lấy từ user
                }

                # Create the report
                report = request.env['hospital.medical.report'].create(report_vals)

                # Generate report data
                report.generate_report()

                # Redirect to report detail
                return request.redirect(f'/clinic/reports/medical/{report.id}')
            except Exception as e:
                _logger.error(f"Error creating report: {e}")

                # Get departments safely
                try:
                    departments = request.env['clinic.department'].search([])
                    staffs = request.env['clinic.staff'].search([])
                except Exception:
                    departments = []
                    staffs = []

                values = {
                    'error': str(e),
                    'departments': departments,
                    'staffs': staffs,
                    'page_name': 'create_medical_report',
                    'datetime': datetime,
                }
                return request.render('reporting_and_data_analysis.medical_report_create_template', values)
        else:
            # Display form
            # Get departments and staffs safely
            try:
                departments = request.env['clinic.department'].search([])
                staffs = request.env['clinic.staff'].search([])
            except Exception:
                departments = []
                staffs = []

            values = {
                'departments': departments,
                'staffs': staffs,
                'page_name': 'create_medical_report',
                'datetime': datetime,
            }
            return request.render('reporting_and_data_analysis.medical_report_create_template', values)

    @http.route('/clinic/reports/medical/<int:report_id>/regenerate', type='http', auth='user', website=True)
    def medical_report_regenerate(self, report_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        report = request.env['hospital.medical.report'].browse(report_id)
        if report.exists():
            report.generate_report()
        return request.redirect(f'/clinic/reports/medical/{report_id}')

    @http.route('/clinic/reports/medical/<int:report_id>/approve', type='http', auth='user', website=True)
    def medical_report_approve(self, report_id, **kwargs):
        # Kiểm tra quyền quản lý
        if not self._check_manager_access():
            return request.redirect('/')

        report = request.env['hospital.medical.report'].browse(report_id)
        if report.exists():
            report.action_approve()
        return request.redirect(f'/clinic/reports/medical/{report_id}')