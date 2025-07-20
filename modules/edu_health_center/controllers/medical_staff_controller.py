# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class MedicalStaffAPI(http.Controller):

    # --- Récupération de tous les personnels médicaux
    @http.route('/api/medical/staff', type='json', auth='user', methods=['GET'], csrf=False)
    def get_medical_staff(self, **kwargs):
        staff = request.env['medical.staff'].sudo().search([])
        return [s.read()[0] for s in staff]

    # --- Détail d’un personnel médical
    @http.route('/api/medical/staff/<int:staff_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_single_staff(self, staff_id):
        staff = request.env['medical.staff'].sudo().browse(staff_id)
        if not staff.exists():
            return {'error': 'Personnel non trouvé'}
        return staff.read()[0]

    # --- Création d’un personnel médical
    @http.route('/api/medical/staff/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_staff(self, **kwargs):
        vals = kwargs
        staff = request.env['medical.staff'].sudo().create(vals)
        return {'id': staff.id, 'message': 'Personnel créé'}

    # --- Mise à jour d’un personnel médical
    @http.route('/api/medical/staff/<int:staff_id>/update', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_staff(self, staff_id, **kwargs):
        staff = request.env['medical.staff'].sudo().browse(staff_id)
        if not staff.exists():
            return {'error': 'Personnel non trouvé'}
        staff.write(kwargs)
        return {'id': staff.id, 'message': 'Mise à jour effectuée'}

    # --- Planning du personnel
    @http.route('/api/medical/staff/<int:staff_id>/schedule', type='json', auth='user', methods=['GET'], csrf=False)
    def get_staff_schedule(self, staff_id):
        schedules = request.env['medical.staff.schedule'].sudo().search([('staff_id', '=', staff_id)])
        return [s.read()[0] for s in schedules]

    # --- Formations du personnel
    @http.route('/api/medical/staff/<int:staff_id>/training', type='json', auth='user', methods=['GET'], csrf=False)
    def get_staff_training(self, staff_id):
        trainings = request.env['medical.staff.training'].sudo().search([('staff_id', '=', staff_id)])
        return [t.read()[0] for t in trainings]
