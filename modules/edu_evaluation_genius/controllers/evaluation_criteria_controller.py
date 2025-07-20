# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class EvaluationCriteriaController(http.Controller):

    # === CRITÈRES D'ÉVALUATION ===

    @http.route('/api/evaluation/criteria', type='json', auth='user')
    def get_all_criteria(self):
        records = request.env['edu.evaluation.criteria'].search([])
        data = records.read([
            'id', 'name', 'code', 'description', 'criteria_type', 'weight',
            'max_points', 'active'
        ])
        return {'status': 200, 'criteria': data}

    @http.route('/api/evaluation/criteria/<int:criteria_id>', type='json', auth='user')
    def get_single_criteria(self, criteria_id):
        record = request.env['edu.evaluation.criteria'].browse(criteria_id)
        if not record.exists():
            return {'status': 404, 'error': 'Critère non trouvé'}
        return {'status': 200, 'criteria': record.read()[0]}

    @http.route('/api/evaluation/criteria', type='json', auth='user', methods=['POST'])
    def create_criteria(self, **kwargs):
        try:
            record = request.env['edu.evaluation.criteria'].create(kwargs)
            return {'status': 201, 'id': record.id}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/evaluation/criteria/<int:criteria_id>', type='json', auth='user', methods=['PUT'])
    def update_criteria(self, criteria_id, **kwargs):
        record = request.env['edu.evaluation.criteria'].browse(criteria_id)
        if not record.exists():
            return {'status': 404, 'error': 'Critère non trouvé'}
        try:
            record.write(kwargs)
            return {'status': 200, 'message': 'Critère mis à jour'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/evaluation/criteria/<int:criteria_id>', type='json', auth='user', methods=['DELETE'])
    def delete_criteria(self, criteria_id):
        record = request.env['edu.evaluation.criteria'].browse(criteria_id)
        if not record.exists():
            return {'status': 404, 'error': 'Critère non trouvé'}
        record.unlink()
        return {'status': 200, 'message': 'Critère supprimé'}

    # === NIVEAUX DE RUBRIQUES ===

    @http.route('/api/evaluation/criteria/<int:criteria_id>/rubrics', type='json', auth='user')
    def get_rubric_levels(self, criteria_id):
        record = request.env['edu.evaluation.criteria'].browse(criteria_id)
        if not record.exists():
            return {'status': 404, 'error': 'Critère non trouvé'}
        levels = record.rubric_level_ids.read([
            'id', 'name', 'points', 'description', 'indicators', 'color_class'
        ])
        return {'status': 200, 'rubric_levels': levels}
