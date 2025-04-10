from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError
import json


class PrescriptionManagementController(http.Controller):
    @http.route('/pharmacy/prescriptions', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def prescription_list(self, **kwargs):
        search_value = kwargs.get('search_value', '')
        patient = False

        # Get all prescriptions by default
        if search_value:
            # Search for patient by code or name
            patient = request.env['clinic.patient'].sudo().search([
                '|', ('code', 'ilike', search_value), ('name', 'ilike', search_value)
            ], limit=1)

            if patient:
                # Get prescriptions for this patient
                prescriptions = request.env['prescription.order'].sudo().search([
                    ('patient_id', '=', patient.id)
                ], order='date desc')
            else:
                # If no patient is found but search was performed, return empty set
                prescriptions = request.env['prescription.order'].sudo().search([])
        else:
            # If no search, get all prescriptions
            prescriptions = request.env['prescription.order'].sudo().search([], order='date desc')

        values = {
            'patient': patient,
            'prescriptions': prescriptions,
            'search_value': search_value,
        }
        return request.render('prescription_management.prescription_list_template', values)

    @http.route('/pharmacy/prescription/<model("prescription.order"):prescription_id>', type='http', auth='public',
                website=True)
    def prescription_detail(self, prescription_id, **kwargs):
        if not prescription_id:
            return request.redirect('/pharmacy/prescriptions')

        values = {
            'prescription': prescription_id,
            'prescription_lines': prescription_id.prescription_line_ids,
        }
        return request.render('prescription_management.prescription_detail_template', values)

    # === PHARMACY PRODUCT MANAGEMENT ===

    @http.route('/pharmacy/products', type='http', auth='public', website=True, methods=['GET'])
    def pharmacy_products(self, **kwargs):
        search = kwargs.get('search', '')
        domain = []

        if search:
            domain = ['|', '|',
                      ('code', 'ilike', search),
                      ('name', 'ilike', search),
                      ('category', 'ilike', search)
                      ]

        pharmacy_products = request.env['pharmacy.product'].sudo().search(domain, order='name')

        values = {
            'pharmacy_products': pharmacy_products,
            'search': search
        }
        return request.render('prescription_management.pharmacy_products_template', values)

    @http.route('/pharmacy/product/<model("pharmacy.product"):product_id>', type='http', auth='public', website=True)
    def pharmacy_product_detail(self, product_id, **kwargs):
        if not product_id:
            return request.redirect('/pharmacy/products')

        values = {
            'product': product_id,
        }
        return request.render('prescription_management.pharmacy_product_detail_template', values)

    @http.route('/pharmacy/product/new', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def pharmacy_product_new(self, **kwargs):
        if request.httprequest.method == 'POST':
            try:
                # Prepare values
                vals = {
                    'name': kwargs.get('name'),
                    'code': kwargs.get('code'),
                    'category': kwargs.get('category'),
                    'manufacturer': kwargs.get('manufacturer'),
                    'uom_id': kwargs.get('uom_id'),
                    'purchase_price': float(kwargs.get('purchase_price', 0)),
                    'unit_price': float(kwargs.get('unit_price', 0)),
                    'quantity': int(kwargs.get('quantity', 0)),
                    'description': kwargs.get('description'),
                    'insurance_covered': kwargs.get('insurance_covered') == 'on',
                }

                # Optional date fields
                if kwargs.get('date'):
                    vals['date'] = kwargs.get('date')
                if kwargs.get('expiry'):
                    vals['expiry'] = kwargs.get('expiry')

                # Validate first, then create the product
                # Perform validation before creating
                purchase_price = float(kwargs.get('purchase_price', 0))
                unit_price = float(kwargs.get('unit_price', 0))

                # Mimic the validation in the model
                if purchase_price <= 0:
                    raise ValidationError('Giá nhập phải lớn hơn 0!')
                if unit_price <= 0:
                    raise ValidationError('Giá bán phải lớn hơn 0!')
                if unit_price < purchase_price:
                    raise ValidationError('Giá bán phải lớn hơn hoặc bằng giá nhập!')

                # Get max profit margin from model
                PharmacyProduct = request.env['pharmacy.product'].sudo()
                # Create a temporary instance to call the instance method
                temp_product = PharmacyProduct.new({})
                max_profit_margin = temp_product._get_max_profit_margin(purchase_price)
                actual_profit_margin = ((unit_price - purchase_price) / purchase_price) * 100

                if actual_profit_margin > max_profit_margin:
                    max_price = purchase_price * (1 + max_profit_margin / 100)
                    raise ValidationError(
                        f"Giá bán vượt quá mức thặng số tối đa cho phép ({max_profit_margin}%)! "
                        f"Giá bán tối đa cho phép là {max_price} VNĐ."
                    )

                # If validation passes, create the product
                product = PharmacyProduct.create(vals)
                return request.redirect('/pharmacy/products')

            except (ValueError, ValidationError) as e:
                values = {
                    'error': str(e),
                    'values': kwargs,
                }
                return request.render('prescription_management.pharmacy_product_form_template', values)

        values = {
            'values': {},
            'edit': False,
        }
        return request.render('prescription_management.pharmacy_product_form_template', values)

    @http.route('/pharmacy/product/<model("pharmacy.product"):product_id>/edit', type='http', auth='user', website=True,
                methods=['GET', 'POST'])
    def pharmacy_product_edit(self, product_id, **kwargs):
        if not product_id:
            return request.redirect('/pharmacy/products')

        if request.httprequest.method == 'POST':
            try:
                # Prepare values
                vals = {
                    'name': kwargs.get('name'),
                    'category': kwargs.get('category'),
                    'manufacturer': kwargs.get('manufacturer'),
                    'uom_id': kwargs.get('uom_id'),
                    'purchase_price': float(kwargs.get('purchase_price', 0)),
                    'unit_price': float(kwargs.get('unit_price', 0)),
                    'quantity': int(kwargs.get('quantity', 0)),
                    'description': kwargs.get('description'),
                    'insurance_covered': kwargs.get('insurance_covered') == 'on',
                }

                # Optional date fields
                if kwargs.get('date'):
                    vals['date'] = kwargs.get('date')
                if kwargs.get('expiry'):
                    vals['expiry'] = kwargs.get('expiry')

                # Validate first, then update the product
                purchase_price = float(kwargs.get('purchase_price', 0))
                unit_price = float(kwargs.get('unit_price', 0))

                # Mimic the validation in the model
                if purchase_price <= 0:
                    raise ValidationError('Giá nhập phải lớn hơn 0!')
                if unit_price <= 0:
                    raise ValidationError('Giá bán phải lớn hơn 0!')
                if unit_price < purchase_price:
                    raise ValidationError('Giá bán phải lớn hơn hoặc bằng giá nhập!')

                # Get max profit margin from model
                PharmacyProduct = request.env['pharmacy.product'].sudo()
                # Create a temporary instance to call the instance method
                temp_product = PharmacyProduct.new({})
                max_profit_margin = temp_product._get_max_profit_margin(purchase_price)
                actual_profit_margin = ((unit_price - purchase_price) / purchase_price) * 100

                if actual_profit_margin > max_profit_margin:
                    max_price = purchase_price * (1 + max_profit_margin / 100)
                    raise ValidationError(
                        f"Giá bán vượt quá mức thặng số tối đa cho phép ({max_profit_margin}%)! "
                        f"Giá bán tối đa cho phép là {max_price} VNĐ."
                    )

                # If validation passes, update the product
                product_id.sudo().write(vals)
                return request.redirect(f'/pharmacy/product/{product_id.id}')

            except (ValueError, ValidationError) as e:
                values = {
                    'error': str(e),
                    'values': kwargs,
                    'product': product_id,
                    'edit': True,
                }
                return request.render('prescription_management.pharmacy_product_form_template', values)

        values = {
            'values': {
                'name': product_id.name,
                'code': product_id.code,
                'category': product_id.category,
                'manufacturer': product_id.manufacturer,
                'uom_id': product_id.uom_id,
                'purchase_price': product_id.purchase_price,
                'unit_price': product_id.unit_price,
                'quantity': product_id.quantity,
                'description': product_id.description,
                'insurance_covered': product_id.insurance_covered,
                'date': product_id.date,
                'expiry': product_id.expiry,
            },
            'product': product_id,
            'edit': True,
        }
        return request.render('prescription_management.pharmacy_product_form_template', values)

    @http.route('/pharmacy/product/<model("pharmacy.product"):product_id>/delete', type='http', auth='user',
                website=True)
    def pharmacy_product_delete(self, product_id, **kwargs):
        if not product_id:
            return request.redirect('/pharmacy/products')

        try:
            product_id.sudo().unlink()
            return request.redirect('/pharmacy/products?deletion_success=1')
        except AccessError:
            return request.redirect('/pharmacy/products?deletion_error=1')

    # === CLINIC SERVICES CRUD ===

    @http.route('/pharmacy/services', type='http', auth='public', website=True, methods=['GET'])
    def clinic_services(self, **kwargs):
        search = kwargs.get('search', '')
        domain = []

        if search:
            domain = [('service_name', 'ilike', search)]

        clinic_services = request.env['clinic.service'].sudo().search(domain, order='service_name')

        values = {
            'clinic_services': clinic_services,
            'search': search
        }
        return request.render('prescription_management.clinic_services_template', values)

    @http.route('/pharmacy/service/<model("clinic.service"):service_id>', type='http', auth='public', website=True)
    def clinic_service_detail(self, service_id, **kwargs):
        if not service_id:
            return request.redirect('/pharmacy/services')

        values = {
            'service': service_id,
        }
        return request.render('prescription_management.clinic_service_detail_template', values)

    @http.route('/pharmacy/service/new', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def clinic_service_new(self, **kwargs):
        if request.httprequest.method == 'POST':
            try:
                # Prepare values
                vals = {
                    'service_name': kwargs.get('service_name'),
                    'price': float(kwargs.get('price', 0)),
                    'description': kwargs.get('description'),
                    'insurance_covered': kwargs.get('insurance_covered') == 'on',
                    'active': kwargs.get('active') == 'on',
                }

                # Create the service
                service = request.env['clinic.service'].sudo().create(vals)
                return request.redirect('/pharmacy/services')

            except (ValueError, ValidationError) as e:
                values = {
                    'error': str(e),
                    'values': kwargs,
                }
                return request.render('prescription_management.clinic_service_form_template', values)

        values = {
            'values': {},
            'edit': False,
        }
        return request.render('prescription_management.clinic_service_form_template', values)

    @http.route('/pharmacy/service/<model("clinic.service"):service_id>/edit', type='http', auth='user', website=True,
                methods=['GET', 'POST'])
    def clinic_service_edit(self, service_id, **kwargs):
        if not service_id:
            return request.redirect('/pharmacy/services')

        if request.httprequest.method == 'POST':
            try:
                # Prepare values
                vals = {
                    'service_name': kwargs.get('service_name'),
                    'price': float(kwargs.get('price', 0)),
                    'description': kwargs.get('description'),
                    'insurance_covered': kwargs.get('insurance_covered') == 'on',
                    'active': kwargs.get('active') == 'on',
                }

                # Update the service
                service_id.sudo().write(vals)
                return request.redirect(f'/pharmacy/service/{service_id.id}')

            except (ValueError, ValidationError) as e:
                values = {
                    'error': str(e),
                    'values': kwargs,
                    'service': service_id,
                    'edit': True,
                }
                return request.render('prescription_management.clinic_service_form_template', values)

        values = {
            'values': {
                'service_name': service_id.service_name,
                'price': service_id.price,
                'description': service_id.description,
                'insurance_covered': service_id.insurance_covered,
                'active': service_id.active,
            },
            'service': service_id,
            'edit': True,
        }
        return request.render('prescription_management.clinic_service_form_template', values)

    @http.route('/pharmacy/service/<model("clinic.service"):service_id>/delete', type='http', auth='user', website=True)
    def clinic_service_delete(self, service_id, **kwargs):
        if not service_id:
            return request.redirect('/pharmacy/services')

        try:
            service_id.sudo().unlink()
            return request.redirect('/pharmacy/services?deletion_success=1')
        except AccessError:
            return request.redirect('/pharmacy/services?deletion_error=1')

    # === PRESCRIPTIONS ===

    @http.route('/pharmacy/new_prescription', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def new_prescription(self, **kwargs):
        if request.httprequest.method == 'POST':
            patient_id = int(kwargs.get('patient_id', 0))
            staff_id = int(kwargs.get('staff_id', 0))
            numdate = float(kwargs.get('numdate', 0))
            notes = kwargs.get('notes', '')

            if not patient_id:
                return json.dumps({'error': _('Patient is required')})

            prescription_vals = {
                'patient_id': patient_id,
                'numdate': numdate,
                'notes': notes,
            }

            if staff_id:
                prescription_vals['staff_id'] = staff_id

            try:
                prescription = request.env['prescription.order'].sudo().create(prescription_vals)
                return request.redirect(f'/pharmacy/prescription/{prescription.id}/edit')
            except Exception as e:
                return json.dumps({'error': str(e)})

        patients = request.env['clinic.patient'].sudo().search([], order='name')
        staff = request.env['clinic.staff'].sudo().search([], order='name')

        values = {
            'patients': patients,
            'staff': staff,
        }
        return request.render('prescription_management.new_prescription_template', values)

    @http.route('/pharmacy/prescription/<model("prescription.order"):prescription_id>/edit', type='http', auth='user',
                website=True, methods=['GET', 'POST'])
    def edit_prescription(self, prescription_id, **kwargs):
        if not prescription_id:
            return request.redirect('/pharmacy/prescriptions')

        if request.httprequest.method == 'POST':
            # Handle form submission for adding a prescription line
            product_id = int(kwargs.get('product_id', 0))
            quantity = float(kwargs.get('quantity', 0))
            dosage = kwargs.get('dosage', '')
            instructions = kwargs.get('instructions', '')

            if not product_id or not quantity or not dosage:
                values = {
                    'prescription': prescription_id,
                    'prescription_lines': prescription_id.prescription_line_ids,
                    'error_message': _('Vui lòng điền đầy đủ các trường bắt buộc'),
                    'products': request.env['pharmacy.product'].sudo().search([], order='name'),
                }
                return request.render('prescription_management.edit_prescription_template', values)

            try:
                product = request.env['pharmacy.product'].sudo().browse(product_id)
                if quantity > product.quantity:
                    values = {
                        'prescription': prescription_id,
                        'prescription_lines': prescription_id.prescription_line_ids,
                        'error_message': f"Số lượng thuốc {product.name} vượt quá tồn kho! Hiện có {product.quantity} {product.uom_id} trong kho.",
                        'products': request.env['pharmacy.product'].sudo().search([], order='name'),
                    }
                    return request.render('prescription_management.edit_prescription_template', values)

                existing_line = request.env['prescription.line'].sudo().search([
                    ('order_id', '=', prescription_id.id),
                    ('product_id', '=', product_id)
                ], limit=1)

                if existing_line:
                    values = {
                        'prescription': prescription_id,
                        'prescription_lines': prescription_id.prescription_line_ids,
                        'error_message': f"Thuốc {product.name} đã tồn tại trong đơn thuốc!",
                        'products': request.env['pharmacy.product'].sudo().search([], order='name'),
                    }
                    return request.render('prescription_management.edit_prescription_template', values)

                request.env['prescription.line'].sudo().create({
                    'order_id': prescription_id.id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'dosage': dosage,
                    'instructions': instructions,
                })
                return request.redirect(f'/pharmacy/prescription/{prescription_id.id}/edit')
            except ValidationError as e:
                values = {
                    'prescription': prescription_id,
                    'prescription_lines': prescription_id.prescription_line_ids,
                    'error_message': str(e),
                    'products': request.env['pharmacy.product'].sudo().search([], order='name'),
                }
                return request.render('prescription_management.edit_prescription_template', values)

        values = {
            'prescription': prescription_id,
            'prescription_lines': prescription_id.prescription_line_ids,
            'products': request.env['pharmacy.product'].sudo().search([], order='name'),
        }
        return request.render('prescription_management.edit_prescription_template', values)

        values = {
            'prescription': prescription_id,
            'prescription_lines': prescription_id.prescription_line_ids,
            'products': request.env['pharmacy.product'].sudo().search([], order='name'),
        }
        return request.render('prescription_management.edit_prescription_template', values)

    @http.route('/pharmacy/prescription/line/<model("prescription.line"):line_id>/delete', type='http', auth='user',
                website=True)
    def delete_prescription_line(self, line_id, **kwargs):
        if not line_id:
            return request.redirect('/pharmacy/prescriptions')

        prescription_id = line_id.order_id.id
        line_id.sudo().unlink()

        return request.redirect(f'/pharmacy/prescription/{prescription_id}/edit')

    # === DASHBOARD & QUICK LINKS ===

    @http.route('/pharmacy', type='http', auth='public', website=True)
    def pharmacy_dashboard(self, **kwargs):
        # Get counts for dashboard
        product_count = request.env['pharmacy.product'].sudo().search_count([])
        prescription_count = request.env['prescription.order'].sudo().search_count([])
        service_count = request.env['clinic.service'].sudo().search_count([])
        low_stock_count = request.env['pharmacy.product'].sudo().search_count([('is_quantity', '=', True)])

        # Get latest prescriptions
        latest_prescriptions = request.env['prescription.order'].sudo().search(
            [], order='date desc', limit=5
        )

        # Get low stock products
        low_stock_products = request.env['pharmacy.product'].sudo().search(
            [('is_quantity', '=', True)], order='quantity', limit=5
        )

        values = {
            'product_count': product_count,
            'prescription_count': prescription_count,
            'service_count': service_count,
            'low_stock_count': low_stock_count,
            'latest_prescriptions': latest_prescriptions,
            'low_stock_products': low_stock_products,
        }
        return request.render('prescription_management.pharmacy_dashboard_template', values)

    @http.route('/pharmacy/prescription/<model("prescription.order"):prescription_id>/update', type='http', auth='user',
                website=True, methods=['GET', 'POST'])
    def update_prescription(self, prescription_id, **kwargs):
        if not prescription_id:
            return request.redirect('/pharmacy/prescriptions')

        if request.httprequest.method == 'POST':
            try:
                # Prepare values to update
                vals = {
                    'patient_id': int(kwargs.get('patient_id')) if kwargs.get(
                        'patient_id') else prescription_id.patient_id.id,
                    'numdate': float(kwargs.get('numdate', 0)) if kwargs.get('numdate') else prescription_id.numdate,
                    'notes': kwargs.get('notes', '') if kwargs.get('notes') is not None else prescription_id.notes,
                }

                # Add staff_id if it exists
                if kwargs.get('staff_id'):
                    vals['staff_id'] = int(kwargs.get('staff_id'))
                elif prescription_id.staff_id:
                    vals['staff_id'] = prescription_id.staff_id.id

                # Update the prescription
                prescription_id.sudo().write(vals)
                return request.redirect(f'/pharmacy/prescription/{prescription_id.id}')

            except Exception as e:
                patients = request.env['clinic.patient'].sudo().search([], order='name')
                staff = request.env['clinic.staff'].sudo().search([], order='name')

                values = {
                    'prescription': prescription_id,
                    'patients': patients,
                    'staff': staff,
                    'error_message': str(e),
                }
                return request.render('prescription_management.update_prescription_template', values)

        # GET request - show the update form
        patients = request.env['clinic.patient'].sudo().search([], order='name')
        staff = request.env['clinic.staff'].sudo().search([], order='name')

        values = {
            'prescription': prescription_id,
            'patients': patients,
            'staff': staff,
        }
        return request.render('prescription_management.update_prescription_template', values)

    @http.route('/pharmacy/prescription/<model("prescription.order"):prescription_id>/delete', type='http', auth='user',
                website=True)
    def delete_prescription(self, prescription_id, **kwargs):
        if not prescription_id:
            return request.redirect('/pharmacy/prescriptions')

        try:
            # First try to get the patient ID to redirect back to their prescriptions
            patient_id = prescription_id.patient_id

            # Delete the prescription
            prescription_id.sudo().unlink()

            # If we had a patient, redirect to their prescription list
            if patient_id:
                return request.redirect(f'/pharmacy/prescriptions?search_value={patient_id.code}')
            else:
                return request.redirect('/pharmacy/prescriptions?deletion_success=1')

        except AccessError:
            return request.redirect('/pharmacy/prescriptions?deletion_error=1')
