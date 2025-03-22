# -*- coding: utf-8 -*-
# from odoo import http


# class ReportingAndDataAnalysis(http.Controller):
#     @http.route('/reporting_and_data_analysis/reporting_and_data_analysis', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reporting_and_data_analysis/reporting_and_data_analysis/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('reporting_and_data_analysis.listing', {
#             'root': '/reporting_and_data_analysis/reporting_and_data_analysis',
#             'objects': http.request.env['reporting_and_data_analysis.reporting_and_data_analysis'].search([]),
#         })

#     @http.route('/reporting_and_data_analysis/reporting_and_data_analysis/objects/<model("reporting_and_data_analysis.reporting_and_data_analysis"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reporting_and_data_analysis.object', {
#             'object': obj
#         })

