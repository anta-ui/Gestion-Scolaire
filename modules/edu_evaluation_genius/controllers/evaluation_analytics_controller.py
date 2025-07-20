# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class EvaluationAnalyticsController(http.Controller):

    @http.route('/api/evaluation/analytics', type='json', auth='user')
    def get_analytics(self, **filters):
        domain = []

        # Traitement des filtres optionnels
        if 'student_id' in filters:
            domain.append(('student_id', '=', filters['student_id']))
        if 'course_id' in filters:
            domain.append(('course_id', '=', filters['course_id']))
        if 'period_id' in filters:
            domain.append(('period_id', '=', filters['period_id']))
        if 'faculty_id' in filters:
            domain.append(('faculty_id', '=', filters['faculty_id']))
        if 'batch_id' in filters:
            domain.append(('batch_id', '=', filters['batch_id']))

        analytics = request.env['edu.evaluation.analytics'].search(domain)
        data = analytics.read([
            'student_name', 'course_name', 'faculty_name', 'evaluation_count', 'average_grade',
            'grade_percentage', 'passed_count', 'failed_count', 'retake_count', 'absent_count',
            'success_rate', 'absence_rate', 'evaluation_date'
        ])
        return {'status': 200, 'results': data}

    @http.route('/api/evaluation/dashboard/<int:dashboard_id>', type='json', auth='user')
    def get_dashboard_metrics(self, dashboard_id):
        record = request.env['edu.evaluation.dashboard'].browse(dashboard_id)
        if not record.exists():
            return {'status': 404, 'error': 'Dashboard non trouvé'}
        
        return {
            'status': 200,
            'dashboard': {
                'name': record.name,
                'description': record.description,
                'total_evaluations': record.total_evaluations,
                'average_grade': record.average_grade,
                'success_rate': record.success_rate
            }
        }

    @http.route('/api/evaluation/dashboards', type='json', auth='user')
    def list_dashboards(self):
        dashboards = request.env['edu.evaluation.dashboard'].search([])
        data = dashboards.read(['id', 'name', 'description'])
        return {'status': 200, 'dashboards': data}
