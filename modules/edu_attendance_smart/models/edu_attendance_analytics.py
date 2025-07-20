# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceAnalytics(models.Model):
    _name = 'edu.attendance.analytics'
    _description = 'Analyses de présence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char('Nom', required=True)
    date = fields.Date('Date', required=True, default=fields.Date.today)
    period_type = fields.Selection([
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('yearly', 'Annuel')
    ], string='Type de période', required=True, default='daily')
    
    # Données d'analyse
    total_sessions = fields.Integer('Total sessions', default=0)
    total_students = fields.Integer('Total étudiants', default=0)
    total_teachers = fields.Integer('Total enseignants', default=0)
    
    present_count = fields.Integer('Présents', default=0)
    absent_count = fields.Integer('Absents', default=0)
    late_count = fields.Integer('En retard', default=0)
    excused_count = fields.Integer('Excusés', default=0)
    
    attendance_rate = fields.Float('Taux de présence (%)', compute='_compute_rates', store=True)
    absence_rate = fields.Float('Taux d\'absence (%)', compute='_compute_rates', store=True)
    late_rate = fields.Float('Taux de retard (%)', compute='_compute_rates', store=True)
    
    # Tendances
    trend_attendance = fields.Selection([
        ('improving', 'Amélioration'),
        ('stable', 'Stable'),
        ('declining', 'Déclin')
    ], string='Tendance présence', compute='_compute_trends')
    
    # Alertes
    alert_count = fields.Integer('Nombre d\'alertes', default=0)
    critical_absences = fields.Integer('Absences critiques', default=0)
    
    # Métadonnées
    created_by = fields.Many2one('res.users', 'Créé par', default=lambda self: self.env.user)
    last_updated = fields.Datetime('Dernière mise à jour', default=fields.Datetime.now)

    @api.depends('present_count', 'absent_count', 'late_count', 'excused_count')
    def _compute_rates(self):
        for record in self:
            total = record.present_count + record.absent_count + record.late_count + record.excused_count
            if total > 0:
                record.attendance_rate = (record.present_count / total) * 100
                record.absence_rate = (record.absent_count / total) * 100
                record.late_rate = (record.late_count / total) * 100
            else:
                record.attendance_rate = 0.0
                record.absence_rate = 0.0
                record.late_rate = 0.0

    @api.depends('attendance_rate')
    def _compute_trends(self):
        for record in self:
            # Logique simple pour déterminer la tendance
            if record.attendance_rate >= 90:
                record.trend_attendance = 'improving'
            elif record.attendance_rate >= 75:
                record.trend_attendance = 'stable'
            else:
                record.trend_attendance = 'declining'

    @api.model
    def generate_daily_analytics(self, target_date=None):
        """Générer les analyses quotidiennes"""
        if not target_date:
            target_date = fields.Date.today()
        
        # Rechercher ou créer l'analyse pour cette date
        analytics = self.search([('date', '=', target_date), ('period_type', '=', 'daily')], limit=1)
        if not analytics:
            analytics = self.create({
                'name': f'Analyse quotidienne - {target_date}',
                'date': target_date,
                'period_type': 'daily'
            })
        
        # Calculer les statistiques
        sessions = self.env['edu.attendance.session'].search([
            ('start_datetime', '>=', datetime.combine(target_date, datetime.min.time())),
            ('start_datetime', '<', datetime.combine(target_date + timedelta(days=1), datetime.min.time()))
        ])
        
        records = self.env['edu.attendance.record'].search([
            ('check_in_time', '>=', datetime.combine(target_date, datetime.min.time())),
            ('check_in_time', '<', datetime.combine(target_date + timedelta(days=1), datetime.min.time()))
        ])
        
        analytics.write({
            'total_sessions': len(sessions),
            'total_students': len(records.mapped('student_id')),
            'total_teachers': len(records.mapped('teacher_id')),
            'present_count': len(records.filtered(lambda r: r.attendance_status == 'present')),
            'absent_count': len(records.filtered(lambda r: r.attendance_status == 'absent')),
            'late_count': len(records.filtered(lambda r: r.attendance_status == 'late')),
            'excused_count': len(records.filtered(lambda r: r.attendance_status == 'excused')),
            'last_updated': fields.Datetime.now()
        })
        
        return analytics

    @api.model
    def generate_weekly_analytics(self, week_start=None):
        """Générer les analyses hebdomadaires"""
        if not week_start:
            week_start = fields.Date.today() - timedelta(days=fields.Date.today().weekday())
        
        analytics = self.search([('date', '=', week_start), ('period_type', '=', 'weekly')], limit=1)
        if not analytics:
            analytics = self.create({
                'name': f'Analyse hebdomadaire - Semaine du {week_start}',
                'date': week_start,
                'period_type': 'weekly'
            })
        
        # Agréger les données quotidiennes
        daily_analytics = self.search([
            ('date', '>=', week_start),
            ('date', '<', week_start + timedelta(days=7)),
            ('period_type', '=', 'daily')
        ])
        
        analytics.write({
            'total_sessions': sum(daily_analytics.mapped('total_sessions')),
            'total_students': len(daily_analytics.mapped('total_students')),
            'total_teachers': len(daily_analytics.mapped('total_teachers')),
            'present_count': sum(daily_analytics.mapped('present_count')),
            'absent_count': sum(daily_analytics.mapped('absent_count')),
            'late_count': sum(daily_analytics.mapped('late_count')),
            'excused_count': sum(daily_analytics.mapped('excused_count')),
            'last_updated': fields.Datetime.now()
        })
        
        return analytics

    def get_analytics_summary(self):
        """Obtenir un résumé des analyses"""
        return {
            'period': f"{self.period_type} - {self.date}",
            'attendance_rate': f"{self.attendance_rate:.1f}%",
            'absence_rate': f"{self.absence_rate:.1f}%",
            'late_rate': f"{self.late_rate:.1f}%",
            'trend': dict(self._fields['trend_attendance'].selection)[self.trend_attendance],
            'total_sessions': self.total_sessions,
            'total_students': self.total_students,
            'alert_count': self.alert_count
        }
