# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class MedicalAPI(http.Controller):

    # === MEDICAL STAFF ===
    @http.route('/api/medical/staff', type='json', auth='user', methods=['GET'], csrf=False)
    def get_medical_staff(self, **kwargs):
        staff = request.env['medical.staff'].sudo().search([])
        return [rec.read()[0] for rec in staff]

    @http.route('/api/medical/staff/<int:staff_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_medical_staff_by_id(self, staff_id, **kwargs):
        staff = request.env['medical.staff'].sudo().browse(staff_id)
        return staff.read()[0] if staff.exists() else {'error': 'Personnel non trouvé'}

    # === SCHEDULES ===
    @http.route('/api/medical/schedules', type='json', auth='user', methods=['GET'], csrf=False)
    def get_schedules(self, **kwargs):
        schedules = request.env['medical.staff.schedule'].sudo().search([])
        return [s.read()[0] for s in schedules]

    # === TRAININGS ===
    @http.route('/api/medical/trainings', type='json', auth='user', methods=['GET'], csrf=False)
    def get_trainings(self, **kwargs):
        trainings = request.env['medical.staff.training'].sudo().search([])
        return [t.read()[0] for t in trainings]

    # === MEDICATION STOCK ===
    @http.route('/api/medication/stock', type='json', auth='user', methods=['GET'], csrf=False)
    def get_medication_stock(self, **kwargs):
        meds = request.env['medication.stock'].sudo().search([])
        return [m.read()[0] for m in meds]

    # === MEDICATION PRESCRIPTIONS ===
    @http.route('/api/medication/prescriptions', type='json', auth='user', methods=['GET'], csrf=False)
    def get_prescriptions(self, **kwargs):
        pres = request.env['medication.prescription'].sudo().search([])
        return [p.read()[0] for p in pres]

    # === MEDICATION ADMINISTRATIONS ===
    @http.route('/api/medication/administrations', type='json', auth='user', methods=['GET'], csrf=False)
    def get_administrations(self, **kwargs):
        admins = request.env['medication.administration'].sudo().search([])
        return [a.read()[0] for a in admins]
