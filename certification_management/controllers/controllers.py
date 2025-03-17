# -*- coding: utf-8 -*-
# from odoo import http


# class CertificationManagement(http.Controller):
#     @http.route('/certification_management/certification_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/certification_management/certification_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('certification_management.listing', {
#             'root': '/certification_management/certification_management',
#             'objects': http.request.env['certification_management.certification_management'].search([]),
#         })

#     @http.route('/certification_management/certification_management/objects/<model("certification_management.certification_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('certification_management.object', {
#             'object': obj
#         })

