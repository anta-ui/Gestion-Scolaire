# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TimetableConstraintAPI(http.Controller):

    @http.route('/api/timetable_constraints', type='json', auth='user', methods=['GET'])
    def list_constraints(self):
        constraints = request.env['edu.timetable.constraint'].sudo().search([])
        return [{
            'id': c.id,
            'name': c.name,
            'type': c.constraint_type,
            'category': c.category,
            'priority': c.priority,
            'active': c.active,
        } for c in constraints]

    @http.route('/api/timetable_constraints/<int:constraint_id>', type='json', auth='user', methods=['GET'])
    def get_constraint(self, constraint_id):
        constraint = request.env['edu.timetable.constraint'].sudo().browse(constraint_id)
        if not constraint.exists():
            return {'error': 'Contrainte non trouvée'}
        return {
            'id': constraint.id,
            'name': constraint.name,
            'description': constraint.description,
            'type': constraint.constraint_type,
            'category': constraint.category,
            'priority': constraint.priority,
            'active': constraint.active,
        }

    @http.route('/api/timetable_constraints', type='json', auth='user', methods=['POST'])
    def create_constraint(self, **kwargs):
        vals = kwargs.get('params', {})
        constraint = request.env['edu.timetable.constraint'].sudo().create(vals)
        return {'id': constraint.id, 'message': 'Contrainte créée avec succès'}

    @http.route('/api/timetable_constraints/<int:constraint_id>', type='json', auth='user', methods=['PUT'])
    def update_constraint(self, constraint_id, **kwargs):
        vals = kwargs.get('params', {})
        constraint = request.env['edu.timetable.constraint'].sudo().browse(constraint_id)
        if not constraint.exists():
            return {'error': 'Contrainte non trouvée'}
        constraint.write(vals)
        return {'message': 'Contrainte mise à jour'}

    @http.route('/api/timetable_constraints/<int:constraint_id>', type='json', auth='user', methods=['DELETE'])
    def delete_constraint(self, constraint_id):
        constraint = request.env['edu.timetable.constraint'].sudo().browse(constraint_id)
        if not constraint.exists():
            return {'error': 'Contrainte non trouvée'}
        constraint.unlink()
        return {'message': 'Contrainte supprimée'}
