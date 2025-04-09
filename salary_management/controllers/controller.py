# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError
import logging

_logger = logging.getLogger(__name__)


class SalaryManagementController(http.Controller):

    # Main salary dashboard
    @http.route('/salary/dashboard', type='http', auth='user', website=True)
    def salary_dashboard(self, **kw):
        return request.render('salary_management.salary_dashboard_template', {})

    # View list of salary sheets
    @http.route('/salary/sheets', type='http', auth='user', website=True)
    def salary_sheets(self, **kw):
        sheets = request.env['clinic.salary.sheet'].sudo().search([])
        values = {
            'sheets': sheets,
        }
        return request.render('salary_management.salary_sheets_template', values)

    # Create or edit a salary sheet
    @http.route('/salary/sheet/<model("clinic.salary.sheet"):sheet>', type='http', auth='user', website=True)
    def salary_sheet_detail(self, sheet=None, **kw):
        if not sheet:
            sheet = request.env['clinic.salary.sheet'].sudo().create({
                'month': kw.get('month'),
                'year': kw.get('year'),
                'state': 'draft'
            })

        values = {
            'sheet': sheet,
            'salaries': sheet.salary_ids,
        }
        return request.render('salary_management.salary_sheet_detail_template', values)

    # Create a new salary sheet form
    @http.route('/salary/sheet/new', type='http', auth='user', website=True)
    def new_salary_sheet(self, **kw):
        years = [(str(year), str(year)) for year in range(2020, 2031)]
        months = [
            ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
            ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
            ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
            ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12')
        ]

        values = {
            'years': years,
            'months': months,
        }
        return request.render('salary_management.salary_sheet_new_template', values)

    # Process the creation of a new salary sheet
    @http.route('/salary/sheet/create', type='http', auth='user', website=True, methods=['POST'])
    def create_salary_sheet(self, **post):
        if post.get('month') and post.get('year'):
            try:
                sheet = request.env['clinic.salary.sheet'].sudo().create({
                    'month': post.get('month'),
                    'year': post.get('year'),
                    'state': 'draft'
                })
                return request.redirect(f'/salary/sheet/{sheet.id}')
            except Exception as e:
                return request.render('salary_management.salary_sheet_error_template', {
                    'error': str(e),
                    'years': [(str(year), str(year)) for year in range(2020, 2031)],
                    'months': [
                        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
                        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
                        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
                        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12')
                    ],
                })
        return request.redirect('/salary/sheets')

    # Generate salary records for all staff
    @http.route('/salary/sheet/<int:sheet_id>/generate', type='http', auth='user', website=True)
    def generate_salary_records(self, sheet_id, **kw):
        sheet = request.env['clinic.salary.sheet'].sudo().browse(sheet_id)
        if sheet:
            try:
                sheet.action_create_salary_records()
                return request.redirect(f'/salary/sheet/{sheet.id}')
            except Exception as e:
                return request.render('salary_management.operation_error_template', {
                    'error': str(e),
                    'back_url': f'/salary/sheet/{sheet.id}'
                })
        return request.redirect('/salary/sheets')

    # View individual salary details
    @http.route('/salary/detail/<model("clinic.staff.salary"):salary>', type='http', auth='user', website=True)
    def salary_detail(self, salary, **kw):
        allowances = request.env['clinic.staff.salary.allowance'].sudo().search([])
        bonuses = request.env['clinic.staff.salary.bonus'].sudo().search([])
        deductions = request.env['clinic.staff.salary.deduction'].sudo().search([])

        values = {
            'salary': salary,
            'all_allowances': allowances,
            'all_bonuses': bonuses,
            'all_deductions': deductions,
        }
        return request.render('salary_management.salary_detail_template', values)

    # Update salary record (add/remove allowances, bonuses, deductions)
    @http.route('/salary/update/<int:salary_id>', type='http', auth='user', website=True, methods=['POST'])
    def update_salary(self, salary_id, **post):
        salary = request.env['clinic.staff.salary'].sudo().browse(salary_id)
        if not salary:
            return request.redirect('/salary/sheets')

        # Update allowances
        if 'allowance_ids' in post:
            allowance_ids = [int(id) for id in request.httprequest.form.getlist('allowance_ids')]
            salary.write({'allowance_ids': [(6, 0, allowance_ids)]})

        # Update bonuses
        if 'bonus_ids' in post:
            bonus_ids = [int(id) for id in request.httprequest.form.getlist('bonus_ids')]
            salary.write({'bonus_ids': [(6, 0, bonus_ids)]})

        # Update deductions
        if 'deduction_ids' in post:
            deduction_ids = [int(id) for id in request.httprequest.form.getlist('deduction_ids')]
            salary.write({'deduction_ids': [(6, 0, deduction_ids)]})

        return request.redirect(f'/salary/detail/{salary_id}')

    # Confirm salary
    @http.route('/salary/confirm/<int:salary_id>', type='http', auth='user', website=True)
    def confirm_salary(self, salary_id, **kw):
        salary = request.env['clinic.staff.salary'].sudo().browse(salary_id)
        if salary and salary.state == 'draft':
            try:
                salary.action_confirm()
                return request.redirect(f'/salary/detail/{salary_id}')
            except Exception as e:
                return request.render('salary_management.operation_error_template', {
                    'error': str(e),
                    'back_url': f'/salary/detail/{salary_id}'
                })
        return request.redirect(f'/salary/detail/{salary_id}')

    # Pay salary
    @http.route('/salary/pay/<int:salary_id>', type='http', auth='user', website=True)
    def pay_salary(self, salary_id, **kw):
        salary = request.env['clinic.staff.salary'].sudo().browse(salary_id)
        if salary and salary.state == 'confirmed':
            try:
                salary.action_pay()
                return request.redirect(f'/salary/detail/{salary_id}')
            except Exception as e:
                return request.render('salary_management.operation_error_template', {
                    'error': str(e),
                    'back_url': f'/salary/detail/{salary_id}'
                })
        return request.redirect(f'/salary/detail/{salary_id}')

    # Manage allowances list
    @http.route('/salary/allowances', type='http', auth='user', website=True)
    def allowances(self, **kw):
        allowances = request.env['clinic.staff.salary.allowance'].sudo().search([])
        values = {
            'allowances': allowances,
        }
        return request.render('salary_management.allowances_template', values)

    # Create new allowance form
    @http.route('/salary/allowance/new', type='http', auth='user', website=True)
    def new_allowance(self, **kw):
        return request.render('salary_management.allowance_form_template', {})

    # Edit allowance form
    @http.route('/salary/allowance/<model("clinic.staff.salary.allowance"):allowance>/edit', type='http', auth='user',
                website=True)
    def edit_allowance(self, allowance, **kw):
        values = {
            'allowance': allowance,
        }
        return request.render('salary_management.allowance_form_template', values)

    # Create or update allowance
    @http.route('/salary/allowance/save', type='http', auth='user', website=True, methods=['POST'])
    def save_allowance(self, **post):
        allowance_id = int(post.get('allowance_id', 0))

        values = {
            'allowance_name': post.get('allowance_name'),
            'amount': float(post.get('amount', 0)),
            'note': post.get('note'),
        }

        if allowance_id:
            allowance = request.env['clinic.staff.salary.allowance'].sudo().browse(allowance_id)
            if allowance:
                allowance.write(values)
        else:
            request.env['clinic.staff.salary.allowance'].sudo().create(values)

        return request.redirect('/salary/allowances')

    # Similar routes for bonuses management
    @http.route('/salary/bonuses', type='http', auth='user', website=True)
    def bonuses(self, **kw):
        bonuses = request.env['clinic.staff.salary.bonus'].sudo().search([])
        values = {
            'bonuses': bonuses,
        }
        return request.render('salary_management.bonuses_template', values)

    @http.route('/salary/bonus/new', type='http', auth='user', website=True)
    def new_bonus(self, **kw):
        return request.render('salary_management.bonus_form_template', {})

    @http.route('/salary/bonus/<model("clinic.staff.salary.bonus"):bonus>/edit', type='http', auth='user', website=True)
    def edit_bonus(self, bonus, **kw):
        values = {
            'bonus': bonus,
        }
        return request.render('salary_management.bonus_form_template', values)

    @http.route('/salary/bonus/save', type='http', auth='user', website=True, methods=['POST'])
    def save_bonus(self, **post):
        bonus_id = int(post.get('bonus_id', 0))

        values = {
            'bonus_name': post.get('bonus_name'),
            'amount': float(post.get('amount', 0)),
            'reason': post.get('reason'),
        }

        if bonus_id:
            bonus = request.env['clinic.staff.salary.bonus'].sudo().browse(bonus_id)
            if bonus:
                bonus.write(values)
        else:
            request.env['clinic.staff.salary.bonus'].sudo().create(values)

        return request.redirect('/salary/bonuses')

    # Similar routes for deductions management
    @http.route('/salary/deductions', type='http', auth='user', website=True)
    def deductions(self, **kw):
        deductions = request.env['clinic.staff.salary.deduction'].sudo().search([])
        values = {
            'deductions': deductions,
        }
        return request.render('salary_management.deductions_template', values)

    @http.route('/salary/deduction/new', type='http', auth='user', website=True)
    def new_deduction(self, **kw):
        return request.render('salary_management.deduction_form_template', {})

    @http.route('/salary/deduction/<model("clinic.staff.salary.deduction"):deduction>/edit', type='http', auth='user',
                website=True)
    def edit_deduction(self, deduction, **kw):
        values = {
            'deduction': deduction,
        }
        return request.render('salary_management.deduction_form_template', values)

    @http.route('/salary/deduction/save', type='http', auth='user', website=True, methods=['POST'])
    def save_deduction(self, **post):
        deduction_id = int(post.get('deduction_id', 0))

        values = {
            'deduction_name': post.get('deduction_name'),
            'rate': float(post.get('rate', 0)),
            'salary_type': post.get('salary_type'),
            'reason': post.get('reason'),
        }

        if deduction_id:
            deduction = request.env['clinic.staff.salary.deduction'].sudo().browse(deduction_id)
            if deduction:
                deduction.write(values)
        else:
            request.env['clinic.staff.salary.deduction'].sudo().create(values)

        return request.redirect('/salary/deductions')

    # Qualification levels management
    @http.route('/salary/qualification_levels', type='http', auth='user', website=True)
    def qualification_levels(self, **kw):
        levels = request.env['clinic.staff.salary.qualification_level'].sudo().search([])
        values = {
            'levels': levels,
        }
        return request.render('salary_management.qualification_levels_template', values)

    @http.route('/salary/qualification_level/new', type='http', auth='user', website=True)
    def new_qualification_level(self, **kw):
        staff_types = request.env['clinic.staff.type'].sudo().search([])
        ranks = [(str(i), str(i)) for i in range(1, 16)]
        values = {
            'staff_types': staff_types,
            'ranks': ranks,
        }
        return request.render('salary_management.qualification_level_form_template', values)

    @http.route('/salary/qualification_level/<model("clinic.staff.salary.qualification_level"):level>/edit',
                type='http', auth='user', website=True)
    def edit_qualification_level(self, level, **kw):
        staff_types = request.env['clinic.staff.type'].sudo().search([])
        ranks = [(str(i), str(i)) for i in range(1, 16)]
        values = {
            'level': level,
            'staff_types': staff_types,
            'ranks': ranks,
        }
        return request.render('salary_management.qualification_level_form_template', values)

    @http.route('/salary/qualification_level/save', type='http', auth='user', website=True, methods=['POST'])
    def save_qualification_level(self, **post):
        level_id = int(post.get('level_id', 0))

        values = {
            'staff_type_id': int(post.get('staff_type_id')),
            'rank': post.get('rank'),
            'salary_factor': float(post.get('salary_factor', 1.0)),
        }

        if level_id:
            level = request.env['clinic.staff.salary.qualification_level'].sudo().browse(level_id)
            if level:
                level.write(values)
        else:
            request.env['clinic.staff.salary.qualification_level'].sudo().create(values)

        return request.redirect('/salary/qualification_levels')
