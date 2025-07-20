# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class TimetableEnhanced(models.Model):
    _name = 'edu.timetable.enhanced'
    _description = 'Emploi du Temps Intelligent'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'academic_year_id desc, name'

    # Informations de base
    name = fields.Char(
        string='Nom de l\'emploi du temps',
        required=True,
        tracking=True
    )
    
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    academic_year_id = fields.Many2one(
        'op.academic.year',
        string='Année académique',
        required=True,
        tracking=True
    )
    
    academic_term_id = fields.Many2one(
        'op.academic.term',
        string='Semestre/Trimestre',
        required=True,
        tracking=True
    )
    
    # Dates et périodes
    start_date = fields.Date(
        string='Date de début',
        required=True,
        tracking=True
    )
    
    end_date = fields.Date(
        string='Date de fin',
        required=True,
        tracking=True
    )
    
    # Configuration
    work_days = fields.Selection([
        ('5', 'Lundi - Vendredi'),
        ('6', 'Lundi - Samedi'),
        ('7', 'Tous les jours'),
    ], string='Jours de travail', default='5', required=True)
    
    daily_hours_start = fields.Float(
        string='Heure de début (h)',
        default=8.0,
        help='Heure de début des cours (format 24h)'
    )
    
    daily_hours_end = fields.Float(
        string='Heure de fin (h)',
        default=17.0,
        help='Heure de fin des cours (format 24h)'
    )
    
    slot_duration = fields.Float(
        string='Durée du créneau (min)',
        default=60.0,
        help='Durée d\'un créneau en minutes'
    )
    
    break_duration = fields.Float(
        string='Durée pause (min)',
        default=15.0,
        help='Durée des pauses entre cours en minutes'
    )
    
    # État et statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('generating', 'Génération en cours'),
        ('generated', 'Généré'),
        ('optimizing', 'Optimisation en cours'),
        ('optimized', 'Optimisé'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ], string='État', default='draft', tracking=True)
    
    # Relations
    schedule_line_ids = fields.One2many(
        'edu.schedule.slot',
        'timetable_id',
        string='Créneaux horaires'
    )
    
    constraint_ids = fields.One2many(
        'edu.timetable.constraint',
        'timetable_id',
        string='Contraintes'
    )
    
    conflict_ids = fields.One2many(
        'edu.timetable.conflict',
        'timetable_id',
        string='Conflits détectés'
    )
    
    # Statistiques
    total_slots = fields.Integer(
        string='Total créneaux',
        compute='_compute_statistics'
    )
    
    filled_slots = fields.Integer(
        string='Créneaux remplis',
        compute='_compute_statistics'
    )
    
    conflict_count = fields.Integer(
        string='Nombre de conflits',
        compute='_compute_statistics'
    )
    
    fill_percentage = fields.Float(
        string='Pourcentage de remplissage',
        compute='_compute_statistics'
    )
    
    # Configuration IA
    ai_enabled = fields.Boolean(
        string='IA activée',
        default=True,
        help='Activer l\'optimisation par IA'
    )
    
    ai_optimization_level = fields.Selection([
        ('basic', 'Basique'),
        ('standard', 'Standard'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert'),
    ], string='Niveau d\'optimisation IA', default='standard')
    
    ai_constraints = fields.Text(
        string='Contraintes IA (JSON)',
        help='Contraintes spécifiques pour l\'IA au format JSON'
    )
    
    last_optimization = fields.Datetime(
        string='Dernière optimisation',
        readonly=True
    )
    
    optimization_score = fields.Float(
        string='Score d\'optimisation',
        readonly=True,
        help='Score de qualité de l\'emploi du temps (0-100)'
    )
    
    # Métadonnées
    active = fields.Boolean(default=True)
    
    created_by_ai = fields.Boolean(
        string='Créé par IA',
        default=False,
        readonly=True
    )
    
    @api.depends('schedule_line_ids', 'conflict_ids')
    def _compute_statistics(self):
        """Calcul des statistiques de l'emploi du temps"""
        for record in self:
            record.total_slots = len(record.schedule_line_ids)
            record.filled_slots = len(record.schedule_line_ids.filtered(lambda x: x.subject_id))
            record.conflict_count = len(record.conflict_ids.filtered(lambda x: x.state == 'active'))
            
            if record.total_slots > 0:
                record.fill_percentage = (record.filled_slots / record.total_slots) * 100
            else:
                record.fill_percentage = 0.0
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validation des dates"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date >= record.end_date:
                    raise ValidationError(_('La date de fin doit être postérieure à la date de début.'))
    
    @api.constrains('daily_hours_start', 'daily_hours_end')
    def _check_hours(self):
        """Validation des heures"""
        for record in self:
            if record.daily_hours_start >= record.daily_hours_end:
                raise ValidationError(_('L\'heure de fin doit être postérieure à l\'heure de début.'))
    
    def action_generate_schedule(self):
        """Générer l'emploi du temps automatiquement"""
        self.ensure_one()
        
        if self.state not in ['draft', 'generated']:
            raise UserError(_('Impossible de générer depuis cet état.'))
        
        # Marquer comme en cours de génération
        self.write({'state': 'generating'})
        
        try:
            # Supprimer les anciens créneaux
            self.schedule_line_ids.unlink()
            
            # Générer la grille de base
            self._generate_base_grid()
            
            # Si IA activée, optimiser
            if self.ai_enabled:
                self._optimize_with_ai()
                self.write({'state': 'optimized'})
            else:
                self.write({'state': 'generated'})
                
            # Détecter les conflits
            self._detect_conflicts()
            
            # Message de succès
            self.message_post(
                body=_('Emploi du temps généré avec succès. %d créneaux créés.') % len(self.schedule_line_ids)
            )
            
        except Exception as e:
            self.write({'state': 'draft'})
            raise UserError(_('Erreur lors de la génération: %s') % str(e))
    
    def _generate_base_grid(self):
        """Générer la grille de base des créneaux"""
        slots = []
        current_date = self.start_date
        
        # Jours de la semaine
        work_days_map = {
            '5': [0, 1, 2, 3, 4],  # Lun-Ven
            '6': [0, 1, 2, 3, 4, 5],  # Lun-Sam
            '7': [0, 1, 2, 3, 4, 5, 6],  # Tous
        }
        
        valid_weekdays = work_days_map[self.work_days]
        
        while current_date <= self.end_date:
            if current_date.weekday() in valid_weekdays:
                # Générer les créneaux pour cette journée
                current_time = self.daily_hours_start
                
                while current_time < self.daily_hours_end:
                    # Créer le créneau
                    start_time = current_time
                    end_time = current_time + (self.slot_duration / 60.0)
                    
                    if end_time <= self.daily_hours_end:
                        slot_vals = {
                            'timetable_id': self.id,
                            'date': current_date,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': self.slot_duration,
                            'day_of_week': str(current_date.weekday()),
                            'slot_number': len(slots) + 1,
                        }
                        slots.append(slot_vals)
                    
                    # Passer au créneau suivant (+ pause)
                    current_time = end_time + (self.break_duration / 60.0)
            
            current_date += timedelta(days=1)
        
        # Créer tous les créneaux
        self.env['edu.schedule.slot'].create(slots)
        
        _logger.info(f'Grille de base générée: {len(slots)} créneaux créés pour {self.name}')
    
    def _optimize_with_ai(self):
        """Optimisation avec IA"""
        # Appeler le moteur d'optimisation IA
        ai_optimizer = self.env['edu.ai.optimizer']
        ai_optimizer.optimize_timetable(self)
        
        self.write({
            'last_optimization': fields.Datetime.now(),
            'created_by_ai': True,
        })
    
    def _detect_conflicts(self):
        """Détecter les conflits dans l'emploi du temps"""
        # Supprimer les anciens conflits
        self.conflict_ids.unlink()
        
        conflict_resolver = self.env['edu.conflict.resolver']
        conflicts = conflict_resolver.detect_conflicts(self)
        
        # Créer les nouveaux conflits
        for conflict_data in conflicts:
            conflict_data['timetable_id'] = self.id
            self.env['edu.timetable.conflict'].create(conflict_data)
    
    def action_optimize(self):
        """Optimiser l'emploi du temps"""
        self.ensure_one()
        
        if not self.ai_enabled:
            raise UserError(_('L\'optimisation IA n\'est pas activée.'))
        
        self.write({'state': 'optimizing'})
        
        try:
            self._optimize_with_ai()
            self._detect_conflicts()
            self.write({'state': 'optimized'})
            
            self.message_post(
                body=_('Emploi du temps optimisé avec succès. Score: %.1f/100') % (self.optimization_score or 0)
            )
            
        except Exception as e:
            self.write({'state': 'generated'})
            raise UserError(_('Erreur lors de l\'optimisation: %s') % str(e))
    
    def action_publish(self):
        """Publier l'emploi du temps"""
        self.ensure_one()
        
        if self.conflict_count > 0:
            raise UserError(_('Impossible de publier avec des conflits actifs. Résolvez d\'abord les conflits.'))
        
        self.write({'state': 'published'})
        
        # Notification aux utilisateurs concernés
        self._notify_publication()
        
        self.message_post(
            body=_('Emploi du temps publié et notifié aux utilisateurs concernés.')
        )
    
    def _notify_publication(self):
        """Notifier la publication de l'emploi du temps"""
        # Notifier les professeurs
        teachers = self.schedule_line_ids.mapped('teacher_id')
        for teacher in teachers:
            if teacher.user_id:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=teacher.user_id.id,
                    summary=_('Nouvel emploi du temps publié'),
                    note=_('L\'emploi du temps "%s" a été publié.') % self.name,
                )
        
        # Notifier les étudiants via leurs classes
        classes = self.schedule_line_ids.mapped('class_id')
        for class_obj in classes:
            students = class_obj.student_ids
            # Envoyer notification push ou email selon configuration
            # TODO: Implémenter système de notification
    
    def action_duplicate(self):
        """Dupliquer l'emploi du temps"""
        self.ensure_one()
        
        new_timetable = self.copy({
            'name': _('%s (Copie)') % self.name,
            'state': 'draft',
            'created_by_ai': False,
            'last_optimization': False,
            'optimization_score': 0.0,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'edu.timetable.enhanced',
            'res_id': new_timetable.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_schedule(self):
        """Ouvrir la vue calendrier"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Emploi du Temps - %s') % self.name,
            'res_model': 'edu.schedule.slot',
            'view_mode': 'calendar,tree,form',
            'domain': [('timetable_id', '=', self.id)],
            'context': {
                'default_timetable_id': self.id,
                'search_default_timetable_id': self.id,
            },
        }
    
    def action_resolve_conflicts(self):
        """Ouvrir l'assistant de résolution de conflits"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Résoudre les conflits'),
            'res_model': 'edu.conflict.resolver.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_timetable_id': self.id,
            },
        }
