# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TimetableConflictAPI(http.Controller):

    @http.route('/api/timetable_conflicts', type='json', auth='user', methods=['GET'])
    def get_all_conflicts(self):
        conflicts = request.env['edu.timetable.conflict'].sudo().search([])
        return [
            {
                'id': conflict.id,
                'title': conflict.title,
                'type': conflict.conflict_type,
                'severity': conflict.severity,
                'state': conflict.state,
                'entity_type': conflict.entity_type,
                'entity_name': conflict.entity_name,
                'slot_ids': conflict.slot_ids.ids,
            }
            for conflict in conflicts
        ]

    @http.route('/api/timetable_conflicts/<int:conflict_id>', type='json', auth='user', methods=['GET'])
    def get_conflict(self, conflict_id):
        conflict = request.env['edu.timetable.conflict'].sudo().browse(conflict_id)
        if not conflict.exists():
            return {'error': 'Conflit non trouvé'}
        return {
            'id': conflict.id,
            'title': conflict.title,
            'description': conflict.description,
            'type': conflict.conflict_type,
            'severity': conflict.severity,
            'state': conflict.state,
            'entity_type': conflict.entity_type,
            'entity_id': conflict.entity_id,
            'entity_name': conflict.entity_name,
            'slot_ids': conflict.slot_ids.ids,
            'suggested_actions': conflict.suggested_actions,
            'auto_resolvable': conflict.auto_resolvable,
            'resolved_date': conflict.resolved_date,
        }

    @http.route('/api/timetable_conflicts/<int:conflict_id>/resolve', type='json', auth='user', methods=['POST'])
    def resolve_conflict(self, conflict_id, **kwargs):
        conflict = request.env['edu.timetable.conflict'].sudo().browse(conflict_id)
        if not conflict.exists():
            return {'error': 'Conflit non trouvé'}
        conflict.action_resolve()
        return {'message': 'Conflit marqué comme résolu'}

    @http.route('/api/timetable_conflicts/<int:conflict_id>/ignore', type='json', auth='user', methods=['POST'])
    def ignore_conflict(self, conflict_id, **kwargs):
        conflict = request.env['edu.timetable.conflict'].sudo().browse(conflict_id)
        if not conflict.exists():
            return {'error': 'Conflit non trouvé'}
        conflict.action_ignore()
        return {'message': 'Conflit ignoré'}

    @http.route('/api/timetable_conflicts/<int:conflict_id>/auto_resolve', type='json', auth='user', methods=['POST'])
    def auto_resolve_conflict(self, conflict_id, **kwargs):
        conflict = request.env['edu.timetable.conflict'].sudo().browse(conflict_id)
        if not conflict.exists():
            return {'error': 'Conflit non trouvé'}
        success = conflict.action_auto_resolve()
        if success:
            return {'message': 'Conflit résolu automatiquement'}
        return {'message': 'La résolution automatique a échoué'}
