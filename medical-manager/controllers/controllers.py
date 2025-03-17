# -*- coding: utf-8 -*-
# from odoo import http


# class Medical-manager(http.Controller):
#     @http.route('/medical-manager/medical-manager', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/medical-manager/medical-manager/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('medical-manager.listing', {
#             'root': '/medical-manager/medical-manager',
#             'objects': http.request.env['medical-manager.medical-manager'].search([]),
#         })

#     @http.route('/medical-manager/medical-manager/objects/<model("medical-manager.medical-manager"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('medical-manager.object', {
#             'object': obj
#         })

