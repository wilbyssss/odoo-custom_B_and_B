# -*- coding: utf-8 -*-
# from odoo import http


# class PrevaCustomReport(http.Controller):
#     @http.route('/preva_custom_report/preva_custom_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/preva_custom_report/preva_custom_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('preva_custom_report.listing', {
#             'root': '/preva_custom_report/preva_custom_report',
#             'objects': http.request.env['preva_custom_report.preva_custom_report'].search([]),
#         })

#     @http.route('/preva_custom_report/preva_custom_report/objects/<model("preva_custom_report.preva_custom_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('preva_custom_report.object', {
#             'object': obj
#         })
