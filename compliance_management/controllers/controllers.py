# -*- coding: utf-8 -*-
# from odoo import http


# class ComplianceManagement(http.Controller):
#     @http.route('/compliance_management/compliance_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/compliance_management/compliance_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('compliance_management.listing', {
#             'root': '/compliance_management/compliance_management',
#             'objects': http.request.env['compliance_management.compliance_management'].search([]),
#         })

#     @http.route('/compliance_management/compliance_management/objects/<model("compliance_management.compliance_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('compliance_management.object', {
#             'object': obj
#         })

