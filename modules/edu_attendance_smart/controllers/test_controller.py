# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class TestController(http.Controller):
    
    @http.route('/test/hello', type='http', auth='public')
    def test_hello(self, **kwargs):
        return "Hello from edu_attendance_smart!" 