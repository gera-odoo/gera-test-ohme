# -*- coding: utf-8 -*-
# from odoo import http


# class Pdcaas(http.Controller):
#     @http.route('/pdcaas/pdcaas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pdcaas/pdcaas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pdcaas.listing', {
#             'root': '/pdcaas/pdcaas',
#             'objects': http.request.env['pdcaas.pdcaas'].search([]),
#         })

#     @http.route('/pdcaas/pdcaas/objects/<model("pdcaas.pdcaas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pdcaas.object', {
#             'object': obj
#         })
