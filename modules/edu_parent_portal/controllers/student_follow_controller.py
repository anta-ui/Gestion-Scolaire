# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class StudentFollowController(http.Controller):

    @http.route('/api/student/follows', type='json', auth='user', methods=['GET'])
    def list_student_follows(self):
        """Liste les suivis des élèves du parent connecté"""
        parent_partner = request.env.user.partner_id
        follows = request.env['edu.student.follow'].sudo().search([
            ('parent_id', '=', parent_partner.id)
        ])

        result = [{
            'id': follow.id,
            'student': follow.student_id.name,
            'average_grade': follow.current_average,
            'total_absences': follow.total_absences,
            'pending_homework': follow.pending_homework,
            'last_notification': follow.last_notification_date,
        } for follow in follows]

        return {'success': True, 'follows': result}

    @http.route('/api/student/follows/<int:follow_id>', type='json', auth='user', methods=['GET'])
    def get_student_follow_detail(self, follow_id):
        """Détails du suivi d'un élève"""
        follow = request.env['edu.student.follow'].sudo().browse(follow_id)
        if not follow.exists():
            return {'success': False, 'error': 'Follow record not found'}

        return {
            'success': True,
            'follow': {
                'student': follow.student_id.name,
                'current_average': follow.current_average,
                'total_absences': follow.total_absences,
                'pending_homework': follow.pending_homework,
                'total_notifications': follow.total_notifications,
                'last_notification': follow.last_notification_date,
                'preferences': {
                    'grades': follow.follow_grades,
                    'attendance': follow.follow_attendance,
                    'homework': follow.follow_homework,
                    'disciplinary': follow.follow_disciplinary,
                    'medical': follow.follow_medical,
                    'grade_alert_threshold': follow.grade_alert_threshold,
                    'absence_alert_threshold': follow.absence_alert_threshold,
                }
            }
        }

    @http.route('/api/student/progress/<int:student_id>', type='json', auth='user', methods=['GET'])
    def student_progress(self, student_id, **kw):
        """Progression académique d'un élève"""
        progresses = request.env['edu.student.progress'].sudo().search([
            ('student_id', '=', student_id)
        ], order='evaluation_date desc', limit=kw.get('limit', 10))

        result = [{
            'subject': progress.subject_id.name,
            'date': progress.evaluation_date,
            'type': progress.progress_type,
            'score': progress.score,
            'max_score': progress.max_score,
            'percentage': progress.percentage,
            'level': progress.level,
            'comments': progress.comments,
            'teacher': progress.teacher_id.name if progress.teacher_id else ''
        } for progress in progresses]

        return {'success': True, 'progress': result}

    @http.route('/api/student/follows', type='json', auth='user', methods=['POST'])
    def create_student_follow(self, **kw):
        """Créer un suivi étudiant"""
        vals = kw.get('data', {})
        vals['parent_id'] = request.env.user.partner_id.id
        follow = request.env['edu.student.follow'].sudo().create(vals)
        return {'success': True, 'follow_id': follow.id}

    @http.route('/api/student/follows/<int:follow_id>', type='json', auth='user', methods=['PUT'])
    def update_student_follow(self, follow_id, **kw):
        """Modifier un suivi étudiant existant"""
        vals = kw.get('data', {})
        follow = request.env['edu.student.follow'].sudo().browse(follow_id)
        if not follow.exists():
            return {'success': False, 'error': 'Follow record not found'}
        follow.write(vals)
        return {'success': True}

    @http.route('/api/student/follows/<int:follow_id>', type='json', auth='user', methods=['DELETE'])
    def delete_student_follow(self, follow_id):
        """Supprimer un suivi étudiant"""
        follow = request.env['edu.student.follow'].sudo().browse(follow_id)
        if not follow.exists():
            return {'success': False, 'error': 'Follow record not found'}
        follow.unlink()
        return {'success': True}

