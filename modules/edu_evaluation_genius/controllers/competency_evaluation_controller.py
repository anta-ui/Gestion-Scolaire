# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json

class CompetencyEvaluationController(http.Controller):

    @http.route('/api/competency_evaluation', type='json', auth='user')
    def get_all_evaluations(self):
        records = request.env['edu.competency.evaluation'].search([])
        data = records.read(['id', 'display_name', 'evaluation_id', 'competency_id', 'percentage', 'score', 'is_acquired'])
        return {'status': 200, 'evaluations': data}

    @http.route('/api/competency_evaluation/<int:rec_id>', type='json', auth='user')
    def get_evaluation(self, rec_id):
        record = request.env['edu.competency.evaluation'].browse(rec_id)
        if record.exists():
            return {
                'status': 200,
                'evaluation': record.read()[0]
            }
        return {'status': 404, 'error': 'Record not found'}

    @http.route('/api/competency_evaluation', type='json', auth='user', methods=['POST'])
    def create_evaluation(self, **kwargs):
        try:
            record = request.env['edu.competency.evaluation'].create(kwargs)
            return {
                'status': 201,
                'id': record.id,
                'message': 'Evaluation créée avec succès'
            }
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/competency_evaluation/<int:rec_id>', type='json', auth='user', methods=['PUT'])
    def update_evaluation(self, rec_id, **kwargs):
        record = request.env['edu.competency.evaluation'].browse(rec_id)
        if not record.exists():
            return {'status': 404, 'error': 'Record not found'}
        try:
            record.write(kwargs)
            return {'status': 200, 'message': 'Évaluation mise à jour avec succès'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/competency_evaluation/<int:rec_id>', type='json', auth='user', methods=['DELETE'])
    def delete_evaluation(self, rec_id):
        record = request.env['edu.competency.evaluation'].browse(rec_id)
        if not record.exists():
            return {'status': 404, 'error': 'Record not found'}
        record.unlink()
        return {'status': 200, 'message': 'Évaluation supprimée'}

    @http.route('/api/competency_statistics', type='json', auth='user', methods=['POST'])
    def get_competency_statistics(self, **kwargs):
        competency_id = kwargs.get('competency_id')
        period_id = kwargs.get('period_id')
        standard_id = kwargs.get('standard_id')
        
        if not competency_id:
            return {'status': 400, 'error': 'competency_id requis'}
        
        stats = request.env['edu.competency.evaluation'].get_competency_statistics(
            competency_id=int(competency_id),
            period_id=int(period_id) if period_id else None,
            standard_id=int(standard_id) if standard_id else None
        )
        return {'status': 200, 'statistics': stats}
