# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class EduStudentFollow(models.Model):
    """Suivi des étudiants par les parents"""
    _name = 'edu.student.follow'
    _description = 'Suivi étudiant'
    _order = 'create_date desc'
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        help="Élève suivi"
    )
    
    parent_id = fields.Many2one(
        'res.partner',
        string='Parent',
        required=True,
        domain=[('is_parent', '=', True)],
        help="Parent qui suit l'élève"
    )
    
    # Paramètres de suivi
    follow_grades = fields.Boolean(
        string='Suivre les notes',
        default=True,
        help="Recevoir notifications pour les notes"
    )
    
    follow_attendance = fields.Boolean(
        string='Suivre les présences',
        default=True,
        help="Recevoir notifications pour les absences"
    )
    
    follow_homework = fields.Boolean(
        string='Suivre les devoirs',
        default=True,
        help="Recevoir notifications pour les devoirs"
    )
    
    follow_disciplinary = fields.Boolean(
        string='Suivre le disciplinaire',
        default=True,
        help="Recevoir notifications disciplinaires"
    )
    
    follow_medical = fields.Boolean(
        string='Suivre le médical',
        default=False,
        help="Recevoir notifications médicales"
    )
    
    # Alertes et seuils
    grade_alert_threshold = fields.Float(
        string='Seuil d\'alerte notes',
        default=10.0,
        help="Seuil en dessous duquel déclencher une alerte"
    )
    
    absence_alert_threshold = fields.Integer(
        string='Seuil d\'alerte absences',
        default=3,
        help="Nombre d'absences déclenchant une alerte"
    )
    
    # Statistiques de suivi
    total_notifications = fields.Integer(
        string='Total notifications',
        compute='_compute_stats',
        help="Nombre total de notifications reçues"
    )
    
    last_notification_date = fields.Datetime(
        string='Dernière notification',
        compute='_compute_stats',
        help="Date de la dernière notification"
    )
    
    # Résumé académique
    current_average = fields.Float(
        string='Moyenne actuelle',
        compute='_compute_academic_stats',
        help="Moyenne générale actuelle"
    )
    
    total_absences = fields.Integer(
        string='Total absences',
        compute='_compute_academic_stats',
        help="Nombre total d'absences"
    )
    
    pending_homework = fields.Integer(
        string='Devoirs en attente',
        compute='_compute_academic_stats',
        help="Nombre de devoirs en attente"
    )
    
    @api.depends('parent_id')
    def _compute_stats(self):
        for record in self:
            notifications = self.env['edu.parent.notification'].search([
                ('recipient_ids', 'in', record.parent_id.user_ids.ids),
                ('student_ids', 'in', [record.student_id.id])
            ])
            record.total_notifications = len(notifications)
            record.last_notification_date = notifications[0].create_date if notifications else False
    
    @api.depends('student_id')
    def _compute_academic_stats(self):
        for record in self:
            # Calculer la moyenne (exemple basique)
            grades = self.env['op.result'].search([('student_id', '=', record.student_id.id)])
            if grades:
                record.current_average = sum(grades.mapped('marks')) / len(grades)
            else:
                record.current_average = 0.0
            
            # Compter les absences récentes
            absences = self.env['op.attendance.sheet.line'].search([
                ('student_id', '=', record.student_id.id),
                ('present', '=', False),
                ('attendance_date', '>=', fields.Date.today() - timedelta(days=30))
            ])
            record.total_absences = len(absences)
            
            # Compter les devoirs en attente
            homework = self.env['op.assignment'].search([
                ('student_ids', 'in', [record.student_id.id]),
                ('submission_date', '>=', fields.Date.today()),
                ('state', '!=', 'submit')
            ])
            record.pending_homework = len(homework)
    
    def action_view_notifications(self):
        """Voir les notifications pour cet élève"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Notifications - {self.student_id.name}',
            'res_model': 'edu.parent.notification',
            'view_mode': 'tree,form',
            'domain': [
                ('recipient_ids', 'in', self.parent_id.user_ids.ids),
                ('student_ids', 'in', [self.student_id.id])
            ],
        }
    
    def action_view_grades(self):
        """Voir les notes de l'élève"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Notes - {self.student_id.name}',
            'res_model': 'op.result',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.student_id.id)],
        }
    
    def action_view_attendance(self):
        """Voir les présences de l'élève"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Présences - {self.student_id.name}',
            'res_model': 'op.attendance.sheet.line',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.student_id.id)],
        }
    
    def check_alerts(self):
        """Vérifier les alertes et envoyer notifications si nécessaire"""
        for record in self:
            # Vérifier alerte notes
            if record.follow_grades and record.current_average < record.grade_alert_threshold:
                record._send_grade_alert()
            
            # Vérifier alerte absences
            if record.follow_attendance and record.total_absences >= record.absence_alert_threshold:
                record._send_absence_alert()
    
    def _send_grade_alert(self):
        """Envoyer alerte de notes"""
        if self.parent_id.user_ids:
            self.env['edu.parent.notification'].create({
                'title': f'Alerte notes - {self.student_id.name}',
                'message': f'La moyenne de {self.student_id.name} ({self.current_average:.2f}) est en dessous du seuil d\'alerte ({self.grade_alert_threshold}).',
                'category': 'grade',
                'notification_type': 'warning',
                'recipient_ids': [(6, 0, self.parent_id.user_ids.ids)],
                'student_ids': [(6, 0, [self.student_id.id])],
                'state': 'sent',
                'send_date': fields.Datetime.now()
            })
    
    def _send_absence_alert(self):
        """Envoyer alerte d'absences"""
        if self.parent_id.user_ids:
            self.env['edu.parent.notification'].create({
                'title': f'Alerte absences - {self.student_id.name}',
                'message': f'{self.student_id.name} a accumulé {self.total_absences} absences ce mois-ci.',
                'category': 'attendance',
                'notification_type': 'warning',
                'recipient_ids': [(6, 0, self.parent_id.user_ids.ids)],
                'student_ids': [(6, 0, [self.student_id.id])],
                'state': 'sent',
                'send_date': fields.Datetime.now()
            })
    
    @api.model
    def run_daily_checks(self):
        """Exécuter les vérifications quotidiennes (appelé par cron)"""
        follows = self.search([])
        follows.check_alerts()


class EduStudentProgress(models.Model):
    """Progression scolaire de l'étudiant"""
    _name = 'edu.student.progress'
    _description = 'Progression étudiant'
    _order = 'evaluation_date desc'
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        help="Élève concerné"
    )
    
    subject_id = fields.Many2one(
        'op.subject',
        string='Matière',
        required=True,
        help="Matière évaluée"
    )
    
    evaluation_date = fields.Date(
        string='Date d\'évaluation',
        required=True,
        default=fields.Date.today,
        help="Date de l'évaluation"
    )
    
    progress_type = fields.Selection([
        ('academic', 'Académique'),
        ('behavioral', 'Comportemental'),
        ('social', 'Social'),
        ('creative', 'Créatif'),
        ('physical', 'Physique')
    ], string='Type de progression', required=True, help="Type de progression")
    
    score = fields.Float(
        string='Score',
        help="Score obtenu"
    )
    
    max_score = fields.Float(
        string='Score maximum',
        help="Score maximum possible"
    )
    
    percentage = fields.Float(
        string='Pourcentage',
        compute='_compute_percentage',
        store=True,
        help="Pourcentage de réussite"
    )
    
    level = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Bien'),
        ('satisfactory', 'Satisfaisant'),
        ('needs_improvement', 'À améliorer'),
        ('unsatisfactory', 'Insuffisant')
    ], string='Niveau', compute='_compute_level', store=True, help="Niveau de performance")
    
    comments = fields.Text(
        string='Commentaires',
        help="Commentaires de l'enseignant"
    )
    
    teacher_id = fields.Many2one(
        'op.faculty',
        string='Enseignant',
        help="Enseignant évaluateur"
    )
    
    @api.depends('score', 'max_score')
    def _compute_percentage(self):
        for record in self:
            if record.max_score > 0:
                record.percentage = (record.score / record.max_score) * 100
            else:
                record.percentage = 0.0
    
    @api.depends('percentage')
    def _compute_level(self):
        for record in self:
            if record.percentage >= 90:
                record.level = 'excellent'
            elif record.percentage >= 75:
                record.level = 'good'
            elif record.percentage >= 60:
                record.level = 'satisfactory'
            elif record.percentage >= 40:
                record.level = 'needs_improvement'
            else:
                record.level = 'unsatisfactory'
