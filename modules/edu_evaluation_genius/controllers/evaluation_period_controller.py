# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import date

class EvaluationPeriodController(http.Controller):

    @http.route('/api/evaluation/periods', type='json', auth='user')
    def list_periods(self, **filters):
        domain = []

        if 'academic_year_id' in filters:
            domain.append(('academic_year_id', '=', filters['academic_year_id']))
        if 'state' in filters:
            domain.append(('state', '=', filters['state']))

        records = request.env['edu.evaluation.period'].search(domain)
        data = records.read([
            'id', 'name', 'code', 'start_date', 'end_date', 'state', 'evaluation_count',
            'student_count', 'completion_rate', 'academic_year_id'
        ])
        return {'status': 200, 'periods': data}

    @http.route('/api/evaluation/period/<int:period_id>', type='json', auth='user')
    def get_period(self, period_id):
        record = request.env['edu.evaluation.period'].browse(period_id)
        if not record.exists():
            return {'status': 404, 'error': 'Période non trouvée'}
        return {'status': 200, 'period': record.read()[0]}

    @http.route('/api/evaluation/period', type='json', auth='user', methods=['POST'])
    def create_period(self, **kwargs):
        try:
            record = request.env['edu.evaluation.period'].create(kwargs)
            return {'status': 201, 'id': record.id}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/evaluation/period/<int:period_id>', type='json', auth='user', methods=['PUT'])
    def update_period(self, period_id, **kwargs):
        record = request.env['edu.evaluation.period'].browse(period_id)
        if not record.exists():
            return {'status': 404, 'error': 'Période non trouvée'}
        try:
            record.write(kwargs)
            return {'status': 200, 'message': 'Période mise à jour'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/evaluation/period/<int:period_id>', type='json', auth='user', methods=['DELETE'])
    def delete_period(self, period_id):
        record = request.env['edu.evaluation.period'].browse(period_id)
        if not record.exists():
            return {'status': 404, 'error': 'Période non trouvée'}
        record.unlink()
        return {'status': 200, 'message': 'Période supprimée'}

    @http.route('/api/evaluation/period/current', type='json', auth='user')
    def get_current_period(self, academic_year_id=None):
        domain = [
            ('start_date', '<=', date.today()),
            ('end_date', '>=', date.today()),
            ('state', 'in', ['open', 'evaluation'])
        ]
        if academic_year_id:
            domain.append(('academic_year_id', '=', academic_year_id))
        record = request.env['edu.evaluation.period'].search(domain, limit=1)
        if not record:
            return {'status': 404, 'error': 'Aucune période active trouvée'}
        return {'status': 200, 'period': record.read()[0]}

    @http.route('/api/evaluation/period/<int:period_id>/action/<string:action>', type='json', auth='user', methods=['POST'])
    def change_period_state(self, period_id, action):
        record = request.env['edu.evaluation.period'].browse(period_id)
        if not record.exists():
            return {'status': 404, 'error': 'Période non trouvée'}

        try:
            if action == 'open':
                record.action_open()
            elif action == 'start':
                record.action_start_evaluations()
            elif action == 'close':
                record.action_close()
            elif action == 'archive':
                record.action_archive()
            elif action == 'reopen':
                record.action_reopen()
            else:
                return {'status': 400, 'error': 'Action invalide'}
            return {'status': 200, 'message': f'État modifié en {record.state}'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}
