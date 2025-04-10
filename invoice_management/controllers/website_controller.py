from odoo import http
from odoo.http import request, _logger
from datetime import datetime, timedelta
import json


class InvoiceWebsiteController(http.Controller):
    # Invoice routes
    @http.route('/invoice/list', type='http', auth='user', website=True)
    def invoice_list(self, **kw):
        # Get filter parameters from request
        filter_state = kw.get('state')
        filter_date_from = kw.get('date_from')
        filter_date_to = kw.get('date_to')

        # Build domain for filtering
        domain = []
        if filter_state and filter_state != 'all':
            domain.append(('state', '=', filter_state))
        if filter_date_from:
            domain.append(('invoice_date', '>=', filter_date_from))
        if filter_date_to:
            domain.append(('invoice_date', '<=', filter_date_to))

        # Get invoices with domain filter
        invoices = request.env['clinic.invoice'].search(domain, order='invoice_date desc, id desc')

        # Get state options for filter dropdown
        state_options = [
            ('all', 'All'),
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled')
        ]

        # Prepare values for template
        values = {
            'invoices': invoices,
            'filter_state': filter_state or 'all',
            'filter_date_from': filter_date_from,
            'filter_date_to': filter_date_to,
            'state_options': state_options,
            'page_name': 'invoice_list',
        }

        return request.render('invoice_management.invoice_list_template', values)

    @http.route('/invoice/view/<int:invoice_id>', type='http', auth='user', website=True)
    def invoice_view(self, invoice_id, **kw):
        invoice = request.env['clinic.invoice'].browse(invoice_id)

        if not invoice.exists():
            return request.redirect('/invoice/list')

        values = {
            'invoice': invoice,
            'page_name': 'invoice_view',
        }

        return request.render('invoice_management.invoice_view_template', values)

    @http.route(['/invoice/create', '/invoice/edit/<int:invoice_id>'], type='http', auth='user', website=True)
    def invoice_form(self, invoice_id=None, **kw):
        invoice = request.env['clinic.invoice'].browse(invoice_id) if invoice_id else False

        # Redirect nếu hóa đơn đã bị hủy - không cho phép chỉnh sửa
        if invoice and invoice.state == 'cancelled':
            return request.redirect(f'/invoice/view/{invoice.id}')

        patients = request.env['clinic.patient'].search([])
        services = request.env['clinic.service'].search([])
        products = request.env['pharmacy.product'].search([('quantity', '>', 0)])

        # Handle POST request (form submission)
        if request.httprequest.method == 'POST':
            try:
                # Extract invoice values and validate
                values, error_message = self.extract_invoice_values(kw)

                if error_message:
                    # If there's an error, re-render the form with the error message
                    return request.render('invoice_management.invoice_form_template', {
                        'invoice': invoice,
                        'patients': patients,
                        'services': services,
                        'products': products,
                        'page_name': 'invoice_form',
                        'edit_mode': bool(invoice_id),
                        'today': datetime.today().strftime('%Y-%m-%d'),
                        'error_message': error_message,
                    })

                if invoice:
                    # Update existing invoice
                    invoice.write(values)
                else:
                    # Create new invoice
                    invoice = request.env['clinic.invoice'].create(values)

                return request.redirect(f'/invoice/view/{invoice.id}')
            except Exception as e:
                # Xử lý bất kỳ ngoại lệ nào khác
                return request.render('invoice_management.invoice_form_template', {
                    'invoice': invoice,
                    'patients': patients,
                    'services': services,
                    'products': products,
                    'page_name': 'invoice_form',
                    'edit_mode': bool(invoice_id),
                    'today': datetime.today().strftime('%Y-%m-%d'),
                    'error_message': str(e),
                })

        # Handle GET request (form display)
        values = {
            'invoice': invoice,
            'patients': patients,
            'services': services,
            'products': products,
            'page_name': 'invoice_form',
            'edit_mode': bool(invoice_id),
            'today': datetime.today().strftime('%Y-%m-%d'),
        }

        return request.render('invoice_management.invoice_form_template', values)

    def extract_invoice_values(self, kw):
        """Extract invoice values from form submission and validate"""
        # Get form object for better array handling
        form = request.httprequest.form

        values = {
            'patient_id': int(form.get('patient_id')),
            'invoice_date': form.get('invoice_date'),
            'note': form.get('note', ''),
        }

        # Process prescription if selected
        prescription_id = form.get('prescription_id')
        if prescription_id and prescription_id.isdigit():
            prescription_id = int(prescription_id)
            prescription = request.env['prescription.order'].browse(prescription_id)
            if prescription.exists() and prescription.patient_id.id == values['patient_id']:
                values['prescription_ids'] = [(4, prescription_id)]

                # If we're adding a prescription, process its products automatically
                product_lines = []
                unique_product_ids = set()  # Track unique product IDs

                for line in prescription.prescription_line_ids:
                    product = line.product_id
                    if not product:
                        continue

                    # Check for duplicate product
                    if product.id in unique_product_ids:
                        return {}, f'Thuốc {product.name} đã tồn tại trong đơn thuốc. Không thể thêm cùng một thuốc nhiều lần.'

                    unique_product_ids.add(product.id)

                    # Check stock quantity
                    if line.quantity > product.quantity:
                        return {}, f'Không đủ số lượng thuốc {product.name} trong kho! (Còn {product.quantity}, cần {line.quantity})'

                    product_line = {
                        'product_id': product.id,
                        'quantity': line.quantity,
                        'price_unit': product.unit_price or 0,
                    }
                    product_lines.append((0, 0, product_line))

                # Only include if there are product lines
                if product_lines:
                    values['product_lines'] = product_lines

        # Process service lines
        service_lines = []
        # Get arrays from form data
        service_ids = form.getlist('service_id[]')
        service_qtys = form.getlist('service_qty[]')
        service_prices = form.getlist('service_price_unit[]')

        # Process each service line
        for i in range(len(service_ids)):
            if i < len(service_qtys) and service_ids[i]:
                try:
                    service_id = int(service_ids[i])
                    quantity = float(service_qtys[i])

                    if service_id > 0 and quantity > 0:
                        # Get the price from the form or fetch from service
                        price_unit = 0
                        if i < len(service_prices) and service_prices[i]:
                            price_unit = float(service_prices[i])

                        # If price is still 0, get it from the service record
                        if price_unit <= 0:
                            service = request.env['clinic.service'].browse(service_id)
                            if service.exists():
                                price_unit = service.price

                        service_line = {
                            'service_id': service_id,
                            'quantity': quantity,
                        }

                        # Only set price_unit if it's greater than 0
                        if price_unit > 0:
                            service_line['price_unit'] = price_unit

                        service_lines.append((0, 0, service_line))
                except (ValueError, TypeError) as e:
                    continue

        # Process product lines (from form, not from prescription)
        product_lines = values.get('product_lines', [])
        # Get arrays from form data
        product_ids = form.getlist('product_id[]')
        product_qtys = form.getlist('product_qty[]')
        product_prices = form.getlist('product_price_unit[]')

        # Track unique product IDs (including any from prescription)
        unique_product_ids = set()
        for line in product_lines:
            unique_product_ids.add(line[2]['product_id'])

        # Process each product line
        for i in range(len(product_ids)):
            if i < len(product_qtys) and product_ids[i]:
                try:
                    product_id = int(product_ids[i])
                    quantity = float(product_qtys[i])

                    if product_id > 0 and quantity > 0:
                        # Check for duplicate product
                        if product_id in unique_product_ids:
                            product = request.env['pharmacy.product'].browse(product_id)
                            return {}, f'Thuốc {product.name} đã được thêm vào hóa đơn. Không thể thêm cùng một thuốc nhiều lần.'

                        unique_product_ids.add(product_id)

                        # Kiểm tra số lượng tồn kho
                        product = request.env['pharmacy.product'].browse(product_id)
                        if product.exists():
                            if quantity > product.quantity:
                                return {}, f'Không đủ số lượng thuốc {product.name} trong kho! (Còn {product.quantity}, cần {quantity})'

                            # Get the price from the form or fetch from product
                            price_unit = 0
                            if i < len(product_prices) and product_prices[i]:
                                price_unit = float(product_prices[i])

                            # If price is still 0, get it from the product record
                            if price_unit <= 0:
                                price_unit = product.unit_price

                            product_line = {
                                'product_id': product_id,
                                'quantity': quantity,
                            }

                            # Only set price_unit if it's greater than 0
                            if price_unit > 0:
                                product_line['price_unit'] = price_unit

                            product_lines.append((0, 0, product_line))
                except (ValueError, TypeError) as e:
                    continue

        # Only include non-empty line arrays
        if service_lines:
            values['service_lines'] = service_lines
        if product_lines:
            values['product_lines'] = product_lines

        return values, None  # Return values and no error message
    @http.route('/invoice/action/<string:action>/<int:invoice_id>', type='http', auth='user', website=True)
    def invoice_action(self, action, invoice_id, **kw):
        invoice = request.env['clinic.invoice'].browse(invoice_id)

        if not invoice.exists():
            return request.redirect('/invoice/list')

        # Perform action based on parameter
        if action == 'confirm' and invoice.state == 'draft':
            invoice.action_confirm()
        elif action == 'pay' and invoice.state == 'confirmed':
            invoice.action_mark_as_paid()
        elif action == 'cancel' and invoice.state in ['draft', 'confirmed']:
            invoice.action_cancel()
        elif action == 'reset' and invoice.state == 'cancelled':
            invoice.action_reset_to_draft()

        return request.redirect(f'/invoice/view/{invoice_id}')

    # API endpoints cho đơn thuốc
    @http.route('/api/prescriptions', type='http', auth='user')
    def get_patient_prescriptions(self, **kw):
        """API endpoint to get prescriptions for a patient"""
        patient_id = kw.get('patient_id')
        if not patient_id:
            return request.make_response(
                json.dumps({'error': 'Patient ID is required'}),
                headers=[('Content-Type', 'application/json')]
            )

        try:
            patient_id = int(patient_id)
            _logger.info(f"Fetching prescriptions for patient ID: {patient_id}")

            prescriptions = request.env['prescription.order'].search([
                ('patient_id', '=', patient_id)
            ])

            _logger.info(f"Found {len(prescriptions)} prescriptions for patient")

            result = {
                'prescriptions': []
            }

            for prescription in prescriptions:
                try:
                    prescription_date_str = ''
                    if hasattr(prescription, 'prescription_date') and prescription.prescription_date:
                        prescription_date_str = prescription.prescription_date.strftime('%d/%m/%Y')

                    result['prescriptions'].append({
                        'id': prescription.id,
                        'name': getattr(prescription, 'name', f"Đơn thuốc #{prescription.id}"),
                        'date': prescription_date_str
                    })
                except Exception as e:
                    _logger.error(f"Error processing prescription {prescription.id}: {str(e)}")

            _logger.info(f"Returning {len(result['prescriptions'])} prescriptions")

            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error in get_patient_prescriptions: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')]
            )
    @http.route('/api/prescription/<int:prescription_id>', type='http', auth='user')
    def get_prescription_details(self, prescription_id, **kw):
        """API endpoint to get detailed prescription information"""
        try:
            # Get prescription
            prescription = request.env['prescription.order'].browse(prescription_id)

            if not prescription.exists():
                return request.make_response(
                    json.dumps({'error': 'Prescription not found'}),
                    headers=[('Content-Type', 'application/json')]
                )

            # Get products from prescription
            result = {
                'products': [{
                    'id': line.product_id.id,
                    'name': line.product_id.name,
                    'quantity': line.quantity,
                    'price': line.product_id.unit_price,
                } for line in prescription.prescription_line_ids if line.product_id]
            }

            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')]
            )

    # Insurance invoice routes
    @http.route('/insurance/list', type='http', auth='user', website=True)
    def insurance_list(self, **kw):
        insurance_invoices = request.env['clinic.invoice.insurance'].search([])

        values = {
            'insurance_invoices': insurance_invoices,
            'page_name': 'insurance_list',
        }

        return request.render('invoice_management.insurance_list_template', values)

    @http.route('/insurance/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def insurance_create(self, **kw):
        if request.httprequest.method == 'POST':
            # Get form data
            date_from = kw.get('date_from')
            date_to = kw.get('date_to')

            if not date_from or not date_to:
                return request.redirect('/insurance/create')

            # Create new insurance invoice
            vals = {
                'date_from': date_from,
                'date_to': date_to,
            }

            insurance = request.env['clinic.invoice.insurance'].create(vals)

            # Trigger onchange to populate invoice lines
            insurance._onchange_date_range()

            return request.redirect(f'/insurance/view/{insurance.id}')

        # GET request - display form
        today = datetime.today()
        first_day = (today.replace(day=1)).strftime('%Y-%m-%d')
        last_day = today.strftime('%Y-%m-%d')

        values = {
            'page_name': 'insurance_form',
            'date_from': first_day,
            'date_to': last_day,
        }

        return request.render('invoice_management.insurance_form_template', values)

    @http.route('/insurance/view/<int:insurance_id>', type='http', auth='user', website=True)
    def insurance_view(self, insurance_id, **kw):
        insurance = request.env['clinic.invoice.insurance'].browse(insurance_id)

        if not insurance.exists():
            return request.redirect('/insurance/list')

        values = {
            'insurance': insurance,
            'page_name': 'insurance_view',
        }

        return request.render('invoice_management.insurance_view_template', values)

    @http.route('/insurance/action/<string:action>/<int:insurance_id>', type='http', auth='user', website=True)
    def insurance_action(self, action, insurance_id, **kw):
        insurance = request.env['clinic.invoice.insurance'].browse(insurance_id)

        if not insurance.exists():
            return request.redirect('/insurance/list')

        # Perform action based on parameter
        if action == 'confirm' and insurance.state == 'draft':
            insurance.action_confirm()
        elif action == 'pay' and insurance.state == 'confirmed':
            insurance.action_pay()
        elif action == 'cancel' and insurance.state in ['draft', 'confirmed']:
            insurance.action_cancel()
        elif action == 'draft' and insurance.state == 'cancelled':
            insurance.action_draft()

        return request.redirect(f'/insurance/view/{insurance_id}')

    # Purchase order routes
    @http.route('/purchase/list', type='http', auth='user', website=True)
    def purchase_list(self, **kw):
        purchase_orders = request.env['clinic.purchase.order'].search([])

        values = {
            'purchase_orders': purchase_orders,
            'page_name': 'purchase_list',
        }

        return request.render('invoice_management.purchase_list_template', values)

    @http.route('/purchase/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def purchase_create(self, **kw):
        if request.httprequest.method == 'POST':
            try:
                # Get basic form data
                purchase_vals = {
                    'date': request.httprequest.form.get('date'),
                    'supplier_name': request.httprequest.form.get('supplier_name'),
                    'note': request.httprequest.form.get('note', ''),
                }

                # Log for debugging
                _logger.info(f"Creating purchase with basic info: {purchase_vals}")

                # Process product lines
                line_vals = []
                form = request.httprequest.form

                # Get arrays from form data
                product_ids = form.getlist('product_id[]')
                quantities = form.getlist('quantity[]')
                price_units = form.getlist('price_unit[]')

                _logger.info(f"Received product_ids: {product_ids}")
                _logger.info(f"Received quantities: {quantities}")
                _logger.info(f"Received price_units: {price_units}")

                # Process each line
                for i in range(len(product_ids)):
                    if i < len(quantities) and i < len(price_units):
                        try:
                            product_id = int(product_ids[i])
                            quantity = int(quantities[i])

                            if product_id > 0 and quantity > 0:
                                # Get product record to get the price if needed
                                product = request.env['pharmacy.product'].browse(product_id)

                                # Get price from form or fallback to product's purchase_price or unit_price
                                try:
                                    price_unit = float(price_units[i])
                                    if price_unit <= 0:
                                        # Fallback to product price
                                        price_unit = product.unit_price or 0
                                except (ValueError, TypeError):
                                    price_unit = product.unit_price or 0

                                _logger.info(
                                    f"Adding line: product_id={product_id}, quantity={quantity}, price_unit={price_unit}")

                                if price_unit > 0:
                                    line_vals.append((0, 0, {
                                        'product_id': product_id,
                                        'quantity': quantity,
                                        'price_unit': price_unit,
                                    }))
                                else:
                                    _logger.warning(f"Product {product_id} has no price, skipping line")
                        except (ValueError, TypeError) as e:
                            _logger.error(f"Error processing line {i}: {e}")
                            continue

                # Ensure we have at least one line
                if not line_vals:
                    _logger.warning("No valid product lines found")
                    return request.render('invoice_management.purchase_form_template', {
                        'error_message': 'Vui lòng thêm ít nhất một sản phẩm hợp lệ vào phiếu nhập.',
                        'products': request.env['pharmacy.product'].search([]),
                        'page_name': 'purchase_form',
                        'today': datetime.today().strftime('%Y-%m-%d'),
                    })

                purchase_vals['line_ids'] = line_vals

                # Create purchase order with tracking disabled to avoid potential issues
                purchase = request.env['clinic.purchase.order'].with_context(tracking_disable=True).create(
                    purchase_vals)
                _logger.info(f"Successfully created purchase order with ID: {purchase.id}")

                return request.redirect(f'/purchase/view/{purchase.id}')

            except Exception as e:
                _logger.error(f"Error creating purchase order: {e}", exc_info=True)
                return request.render('invoice_management.purchase_form_template', {
                    'error_message': f'Đã xảy ra lỗi: {str(e)}',
                    'products': request.env['pharmacy.product'].search([]),
                    'page_name': 'purchase_form',
                    'today': datetime.today().strftime('%Y-%m-%d'),
                })

        # GET request - show form
        products = request.env['pharmacy.product'].search([])

        values = {
            'products': products,
            'page_name': 'purchase_form',
            'today': datetime.today().strftime('%Y-%m-%d'),
        }

        return request.render('invoice_management.purchase_form_template', values)

    @http.route('/purchase/view/<int:purchase_id>', type='http', auth='user', website=True)
    def purchase_view(self, purchase_id, **kw):
        purchase = request.env['clinic.purchase.order'].browse(purchase_id)

        if not purchase.exists():
            return request.redirect('/purchase/list')

        values = {
            'purchase': purchase,
            'page_name': 'purchase_view',
        }

        return request.render('invoice_management.purchase_view_template', values)

    @http.route('/purchase/action/<string:action>/<int:purchase_id>', type='http', auth='user', website=True)
    def purchase_action(self, action, purchase_id, **kw):
        purchase = request.env['clinic.purchase.order'].browse(purchase_id)

        if not purchase.exists():
            return request.redirect('/purchase/list')

        # Perform action based on parameter
        if action == 'confirm' and purchase.state == 'draft':
            purchase.action_confirm()
        elif action == 'pay' and purchase.state == 'confirmed':
            purchase.action_pay()

        return request.redirect(f'/purchase/view/{purchase_id}')

    # Statistics routes
    @http.route('/statistics/dashboard', type='http', auth='user', website=True)
    def statistics_dashboard(self, **kw):
        # Get latest statistics or create monthly stats if none exists
        statistics = request.env['clinic.statistics'].search([], limit=1, order='id desc')
        if not statistics:
            today = datetime.today()
            first_day = today.replace(day=1).strftime('%Y-%m-%d')
            last_day = today.strftime('%Y-%m-%d')
            statistics = request.env['clinic.statistics'].create_statistics(first_day, last_day)

        values = {
            'statistics': statistics,
            'page_name': 'statistics_dashboard',
        }

        return request.render('invoice_management.statistics_dashboard_template', values)

    @http.route('/statistics/generate', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def statistics_generate(self, **kw):
        if request.httprequest.method == 'POST':
            date_from = kw.get('date_from')
            date_to = kw.get('date_to')

            if date_from and date_to:
                statistics = request.env['clinic.statistics'].create_statistics(date_from, date_to)
                return request.redirect(f'/statistics/view/{statistics.id}')

        # GET request - display form
        today = datetime.today()
        values = {
            'page_name': 'statistics_generate',
            'today': today.strftime('%Y-%m-%d'),
            'month_start': today.replace(day=1).strftime('%Y-%m-%d'),
        }

        return request.render('invoice_management.statistics_generate_template', values)

    @http.route('/statistics/view/<int:statistics_id>', type='http', auth='user', website=True)
    def statistics_view(self, statistics_id, **kw):
        statistics = request.env['clinic.statistics'].browse(statistics_id)

        if not statistics.exists():
            return request.redirect('/statistics/dashboard')

        values = {
            'statistics': statistics,
            'page_name': 'statistics_view',
        }

        # Prepare chart data
        daily_labels = []
        daily_revenue = []
        daily_service = []
        daily_medicine = []

        for day in statistics.daily_stats_ids:
            daily_labels.append(day.date.strftime('%d/%m/%Y'))
            daily_revenue.append(day.total_revenue)
            daily_service.append(day.service_revenue)
            daily_medicine.append(day.medicine_revenue)

        values['chart_labels'] = json.dumps(daily_labels)
        values['chart_revenue'] = json.dumps(daily_revenue)
        values['chart_service'] = json.dumps(daily_service)
        values['chart_medicine'] = json.dumps(daily_medicine)

        return request.render('invoice_management.statistics_view_template', values)

    @http.route('/statistics/print/<int:statistics_id>', type='http', auth='user', website=True)
    def statistics_print(self, statistics_id, **kw):
        # Redirect to the PDF report download URL
        return request.redirect(f'/report/statistics_pdf/{statistics_id}')