# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TestPaymentMethod(models.Model):
    _name = 'test.payment.method'
    _description = 'Test Payment Method'
    
    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)
