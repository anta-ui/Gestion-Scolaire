# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TimetableConstraintController(http.Controller):

    @http.route('/api/timetable_constraints', type='json', auth='user', methods=['GET'])
    def get_all_constraints(self):
        constraints = request.env['edu.timetable.constraint'].sudo().search([])
        return [self._serialize_constraint(c) for c in constraints]

    @http.route('/api/timetable_constraints/<int:constraint_id>', type='json', auth='user', methods=['GET'])
    def get_constraint(self, constraint_id):
        constraint = request.env['edu.timetable.constraint'].sudo().browse(constraint_id)
        if not constraint.exists():
            return {'error': 'Constraint not found'}
        return self._serialize_constraint(constraint)

    @http.route('/api/timetable_constraints', type='json', auth='user', methods=['POST'])
    def create_constraint(self, **kwargs):
        vals = kwargs.get('params') or {}
        new_constraint = request.env['edu.timetable.constraint'].sudo().create(vals)
        return {'id': new_constraint.id}

    @http.route('/api/timetable_constraints/<int:constraint_id>', type='json', auth='user', methods=['PUT'])
    def update_constraint(self, constraint_id, **kwargs):
        constraint = request.env['edu.timetable.constraint'].sudo().browse(constraint_id)
        if not constraint.exists():
            return {'error': 'Constraint not found'}
        vals = kwargs.get('params') or {}
        constraint.write(vals)
        return {'updated': True}

    @http.route('/api/timetable_constraints/<int:constraint_id>', type='json', auth='user', methods=['DELETE'])
    def delete_constraint(self, constraint_id):
        constraint = request.env['edu.timetable.constraint'].sudo().browse(constraint_id)
        if not constraint.exists():
            return {'error': 'Constraint not found'}
        constraint.unlink()
        return {'deleted': True}

    def _serialize_constraint(self, c):
        return {
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'constraint_type': c.constraint_type,
            'category': c.category,
            'timetable_id': c.timetable_id.id,
            'teacher_ids': c.teacher_ids.ids,
            'student_ids': c.student_ids.ids,
            'class_ids': c.class_ids.ids,
            'room_ids': c.room_ids.ids,
            'subject_ids': c.subject_ids.ids,
            'time_constraint_type': c.time_constraint_type,
            'start_time': c.start_time,
            'end_time': c.end_time,
            'allowed_days': c.allowed_days,
            'forbidden_days': c.forbidden_days,
            'min_capacity': c.min_capacity,
            'max_capacity': c.max_capacity,
            'required_equipment_ids': c.required_equipment_ids.ids,
            'max_per_day': c.max_per_day,
            'min_gap_hours': c.min_gap_hours,
            'max_consecutive': c.max_consecutive,
            'priority': c.priority,
            'weight': c.weight,
            'active': c.active,
            'is_violated': c.is_violated,
            'violation_count': c.violation_count,
            'custom_logic': c.custom_logic,
            'parameters': c.parameters,
            'created_by_ai': c.created_by_ai,
            'last_check': c.last_check,
        }
