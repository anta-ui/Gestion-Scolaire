# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class GradeAverageController(http.Controller):

    @http.route('/api/grade/averages', type='json', auth='user')
    def list_averages(self, **filters):
        domain = []

        if 'student_id' in filters:
            domain.append(('student_id', '=', filters['student_id']))
        if 'period_id' in filters:
            domain.append(('period_id', '=', filters['period_id']))
        if 'course_id' in filters:
            domain.append(('course_id', '=', filters['course_id']))
        if 'average_type' in filters:
            domain.append(('average_type', '=', filters['average_type']))

        records = request.env['edu.grade.average'].search(domain)
        data = records.read([
            'id', 'display_name', 'student_id', 'period_id', 'course_id',
            'competency_id', 'average_type', 'weighted_average', 'simple_average',
            'percentage', 'grade_letter', 'evaluation_count', 'is_final'
        ])
        return {'status': 200, 'averages': data}

    @http.route('/api/grade/average/<int:avg_id>', type='json', auth='user')
    def get_average(self, avg_id):
        record = request.env['edu.grade.average'].browse(avg_id)
        if not record.exists():
            return {'status': 404, 'error': 'Moyenne non trouvée'}
        return {'status': 200, 'average': record.read()[0]}

    @http.route('/api/grade/average/<int:avg_id>/recalculate', type='json', auth='user', methods=['POST'])
    def recalculate_average(self, avg_id):
        record = request.env['edu.grade.average'].browse(avg_id)
        if not record.exists():
            return {'status': 404, 'error': 'Moyenne non trouvée'}
        record.action_recalculate()
        return {'status': 200, 'message': 'Moyenne recalculée'}

    @http.route('/api/grade/average/<int:avg_id>/finalize', type='json', auth='user', methods=['POST'])
    def finalize_average(self, avg_id):
        record = request.env['edu.grade.average'].browse(avg_id)
        if not record.exists():
            return {'status': 404, 'error': 'Moyenne non trouvée'}
        record.action_set_final()
        return {'status': 200, 'message': 'Moyenne marquée comme finale'}

    @http.route('/api/grade/averages/bulk_create', type='json', auth='user', methods=['POST'])
    def bulk_create_averages(self, **kwargs):
        wizard = request.env['edu.grade.average.wizard'].create({
            'period_id': kwargs.get('period_id'),
            'batch_ids': [(6, 0, kwargs.get('batch_ids', []))],
            'course_ids': [(6, 0, kwargs.get('course_ids', []))],
            'average_type': kwargs.get('average_type')
        })
        return wizard.action_create_averages()
