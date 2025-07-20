# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class EvaluationTypeController(http.Controller):

    @http.route('/api/evaluation/types', type='json', auth='user')
    def list_evaluation_types(self):
        records = request.env['edu.evaluation.type'].search([])
        data = records.read([
            'id', 'name', 'code', 'description', 'coefficient', 'duration',
            'allow_retake', 'max_retakes', 'is_continuous', 'require_justification',
            'evaluation_count', 'active'
        ])
        return {'status': 200, 'evaluation_types': data}

    @http.route('/api/evaluation/types/<int:type_id>', type='json', auth='user')
    def get_evaluation_type(self, type_id):
        record = request.env['edu.evaluation.type'].browse(type_id)
        if not record.exists():
            return {'status': 404, 'error': 'Type d\'évaluation non trouvé'}
        return {'status': 200, 'evaluation_type': record.read()[0]}

    @http.route('/api/evaluation/types', type='json', auth='user', methods=['POST'])
    def create_evaluation_type(self, **kwargs):
        try:
            record = request.env['edu.evaluation.type'].create(kwargs)
            return {'status': 201, 'id': record.id}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/evaluation/types/<int:type_id>', type='json', auth='user', methods=['PUT'])
    def update_evaluation_type(self, type_id, **kwargs):
        record = request.env['edu.evaluation.type'].browse(type_id)
        if not record.exists():
            return {'status': 404, 'error': 'Type d\'évaluation non trouvé'}
        try:
            record.write(kwargs)
            return {'status': 200, 'message': 'Type d\'évaluation mis à jour'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/evaluation/types/<int:type_id>', type='json', auth='user', methods=['DELETE'])
    def delete_evaluation_type(self, type_id):
        record = request.env['edu.evaluation.type'].browse(type_id)
        if not record.exists():
            return {'status': 404, 'error': 'Type d\'évaluation non trouvé'}
        record.unlink()
        return {'status': 200, 'message': 'Type d\'évaluation supprimé'}
