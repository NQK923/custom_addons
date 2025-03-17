# -*- coding: utf-8 -*-
# from odoo import http


# class HealthcareManagement(http.Controller):
#     @http.route('/healthcare_management/healthcare_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/healthcare_management/healthcare_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('healthcare_management.listing', {
#             'root': '/healthcare_management/healthcare_management',
#             'objects': http.request.env['healthcare_management.healthcare_management'].search([]),
#         })

#     @http.route('/healthcare_management/healthcare_management/objects/<model("healthcare_management.healthcare_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('healthcare_management.object', {
#             'object': obj
#         })

