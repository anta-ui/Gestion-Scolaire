# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class EvaluationController(http.Controller):

    # === ÉVALUATION ===

    @http.route('/api/evaluations', type='json', auth='user')
    def list_evaluations(self, **filters):
        domain = []

        for field in ['student_id', 'course_id', 'faculty_id', 'period_id']:
            if filters.get(field):
                domain.append((field, '=', filters[field]))

        records = request.env['edu.evaluation'].search(domain, limit=100)
        data = records.read([
            'id', 'name', 'code', 'date', 'grade', 'grade_percentage', 'grade_letter',
            'student_id', 'course_id', 'faculty_id', 'evaluation_type_id',
            'period_id', 'state', 'is_absent', 'is_retake'
        ])
        return {'status': 200, 'evaluations': data}

    @http.route('/api/evaluation/<int:eval_id>', type='json', auth='user')
    def get_evaluation(self, eval_id):
        record = request.env['edu.evaluation'].browse(eval_id)
        if not record.exists():
            return {'status': 404, 'error': 'Évaluation non trouvée'}
        return {'status': 200, 'evaluation': record.read()[0]}

    @http.route('/api/evaluation', type='json', auth='user', methods=['POST'])
    def create_evaluation(self, **kwargs):
        try:
            record = request.env['edu.evaluation'].create(kwargs)
            return {'status': 201, 'id': record.id}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/evaluation/<int:eval_id>', type='json', auth='user', methods=['PUT'])
    def update_evaluation(self, eval_id, **kwargs):
        record = request.env['edu.evaluation'].browse(eval_id)
        if not record.exists():
            return {'status': 404, 'error': 'Évaluation non trouvée'}
        try:
            record.write(kwargs)
            return {'status': 200, 'message': 'Évaluation mise à jour'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/evaluation/<int:eval_id>', type='json', auth='user', methods=['DELETE'])
    def delete_evaluation(self, eval_id):
        record = request.env['edu.evaluation'].browse(eval_id)
        if not record.exists():
            return {'status': 404, 'error': 'Évaluation non trouvée'}
        record.unlink()
        return {'status': 200, 'message': 'Évaluation supprimée'}

    @http.route('/api/evaluation/<int:eval_id>/action/<string:action>', type='json', auth='user', methods=['POST'])
    def change_state(self, eval_id, action):
        record = request.env['edu.evaluation'].browse(eval_id)
        if not record.exists():
            return {'status': 404, 'error': 'Évaluation non trouvée'}
        try:
            if action == 'confirm':
                record.action_confirm()
            elif action == 'publish':
                record.action_publish()
            elif action == 'archive':
                record.action_archive()
            elif action == 'draft':
                record.action_back_to_draft()
            elif action == 'retake':
                return record.action_create_retake()
            else:
                return {'status': 400, 'error': 'Action invalide'}
            return {'status': 200, 'message': f"Action '{action}' effectuée"}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    # === LIGNES DE CRITÈRES ===

    @http.route('/api/evaluation/<int:eval_id>/lines', type='json', auth='user')
    def get_evaluation_lines(self, eval_id):
        record = request.env['edu.evaluation'].browse(eval_id)
        if not record.exists():
            return {'status': 404, 'error': 'Évaluation non trouvée'}
        lines = record.evaluation_line_ids.read([
            'id', 'criteria_id', 'points', 'max_points', 'percentage', 'rubric_level_id', 'comment'
        ])
        return {'status': 200, 'lines': lines}
