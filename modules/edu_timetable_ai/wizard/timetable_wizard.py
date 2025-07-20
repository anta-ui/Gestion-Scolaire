# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class TimetableGenerationWizard(models.TransientModel):
    _name = 'edu.timetable.generation.wizard'
    _description = 'Assistant de génération d\'emploi du temps'

    # Configuration de base
    name = fields.Char(
        string='Nom de l\'emploi du temps',
        required=True,
        default=lambda self: _('Emploi du temps %s') % fields.Date.today().strftime('%Y-%m-%d')
    )
    
    academic_year_id = fields.Many2one(
        'op.academic.year',
        string='Année académique',
        required=True,
        default=lambda self: self.env['op.academic.year'].search([('active', '=', True)], limit=1)
    )
    
    academic_term_id = fields.Many2one(
        'op.academic.term',
        string='Semestre/Trimestre',
        required=True
    )
    
    start_date = fields.Date(
        string='Date de début',
        required=True,
        default=fields.Date.today
    )
    
    end_date = fields.Date(
        string='Date de fin',
        required=True
    )
    
    # Configuration horaire
    work_days = fields.Selection([
        ('5', 'Lundi - Vendredi'),
        ('6', 'Lundi - Samedi'),
        ('7', 'Tous les jours'),
    ], string='Jours de travail', default='5', required=True)
    
    daily_hours_start = fields.Float(
        string='Heure de début',
        default=8.0,
        required=True
    )
    
    daily_hours_end = fields.Float(
        string='Heure de fin',
        default=17.0,
        required=True
    )
    
    slot_duration = fields.Float(
        string='Durée du créneau (min)',
        default=60.0,
        required=True
    )
    
    break_duration = fields.Float(
        string='Durée pause (min)',
        default=15.0,
        required=True
    )
    
    # Sélection des entités
    class_ids = fields.Many2many(
        'op.batch',
        string='Classes à inclure'
    )
    
    teacher_ids = fields.Many2many(
        'op.faculty',
        string='Professeurs à inclure'
    )
    
    subject_ids = fields.Many2many(
        'op.subject',
        string='Matières à inclure'
    )
    
    room_ids = fields.Many2many(
        'edu.room.enhanced',
        string='Salles à utiliser'
    )
    
    # Options de génération
    generation_method = fields.Selection([
        ('manual', 'Grille vide'),
        ('semi_auto', 'Semi-automatique'),
        ('full_auto', 'Entièrement automatique'),
        ('ai_optimized', 'Optimisé par IA'),
    ], string='Méthode de génération', default='ai_optimized', required=True)
    
    use_ai = fields.Boolean(
        string='Utiliser l\'IA',
        default=True,
        help='Activer l\'optimisation par intelligence artificielle'
    )
    
    ai_optimization_level = fields.Selection([
        ('basic', 'Basique'),
        ('standard', 'Standard'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert'),
    ], string='Niveau d\'optimisation IA', default='standard')
    
    create_constraints = fields.Boolean(
        string='Créer contraintes automatiques',
        default=True,
        help='Créer automatiquement des contraintes de base'
    )
    
    # Configuration avancée
    max_slots_per_day = fields.Integer(
        string='Maximum de créneaux par jour',
        default=6
    )
    
    min_break_between_classes = fields.Float(
        string='Pause minimale entre cours (min)',
        default=15.0
    )
    
    allow_back_to_back = fields.Boolean(
        string='Autoriser les cours consécutifs',
        default=True
    )
    
    # État du wizard
    step = fields.Selection([
        ('config', 'Configuration'),
        ('entities', 'Sélection des entités'),
        ('constraints', 'Contraintes'),
        ('generation', 'Génération'),
        ('review', 'Révision'),
    ], string='Étape', default='config')
    
    def action_next_step(self):
        """Passer à l'étape suivante"""
        self.ensure_one()
        
        if self.step == 'config':
            self._validate_config()
            self.step = 'entities'
        elif self.step == 'entities':
            self._validate_entities()
            self.step = 'constraints'
        elif self.step == 'constraints':
            self.step = 'generation'
        elif self.step == 'generation':
            self._generate_timetable()
            self.step = 'review'
        
        return self._reload_wizard()
    
    def action_previous_step(self):
        """Revenir à l'étape précédente"""
        self.ensure_one()
        
        if self.step == 'entities':
            self.step = 'config'
        elif self.step == 'constraints':
            self.step = 'entities'
        elif self.step == 'generation':
            self.step = 'constraints'
        elif self.step == 'review':
            self.step = 'generation'
        
        return self._reload_wizard()
    
    def _validate_config(self):
        """Valider la configuration"""
        if self.start_date >= self.end_date:
            raise ValidationError(_('La date de fin doit être postérieure à la date de début.'))
        
        if self.daily_hours_start >= self.daily_hours_end:
            raise ValidationError(_('L\'heure de fin doit être postérieure à l\'heure de début.'))
        
        if self.slot_duration <= 0:
            raise ValidationError(_('La durée du créneau doit être positive.'))
    
    def _validate_entities(self):
        """Valider la sélection des entités"""
        if self.generation_method != 'manual':
            if not self.class_ids:
                raise ValidationError(_('Veuillez sélectionner au moins une classe.'))
            
            if not self.teacher_ids:
                raise ValidationError(_('Veuillez sélectionner au moins un professeur.'))
            
            if not self.subject_ids:
                raise ValidationError(_('Veuillez sélectionner au moins une matière.'))
    
    def _generate_timetable(self):
        """Générer l'emploi du temps"""
        # Créer l'emploi du temps
        timetable_vals = {
            'name': self.name,
            'academic_year_id': self.academic_year_id.id,
            'academic_term_id': self.academic_term_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'work_days': self.work_days,
            'daily_hours_start': self.daily_hours_start,
            'daily_hours_end': self.daily_hours_end,
            'slot_duration': self.slot_duration,
            'break_duration': self.break_duration,
            'ai_enabled': self.use_ai,
            'ai_optimization_level': self.ai_optimization_level,
        }
        
        timetable = self.env['edu.timetable.enhanced'].create(timetable_vals)
        
        # Créer les contraintes automatiques si demandé
        if self.create_constraints:
            self.env['edu.timetable.constraint'].create_ai_constraints(timetable.id)
        
        # Générer selon la méthode choisie
        if self.generation_method == 'manual':
            timetable.action_generate_schedule()
        elif self.generation_method in ['semi_auto', 'full_auto', 'ai_optimized']:
            timetable.action_generate_schedule()
            
            if self.use_ai:
                timetable.action_optimize()
        
        # Stocker l'ID pour la révision
        self.generated_timetable_id = timetable.id
        
        return timetable
    
    def _reload_wizard(self):
        """Recharger le wizard"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_finish(self):
        """Terminer et ouvrir l'emploi du temps généré"""
        self.ensure_one()
        
        if hasattr(self, 'generated_timetable_id'):
            return {
                'type': 'ir.actions.act_window',
                'name': _('Emploi du temps généré'),
                'res_model': 'edu.timetable.enhanced',
                'res_id': self.generated_timetable_id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {'type': 'ir.actions.act_window_close'}


class ConflictResolutionWizard(models.TransientModel):
    _name = 'edu.conflict.resolution.wizard'
    _description = 'Assistant de résolution de conflits'

    conflict_id = fields.Many2one(
        'edu.timetable.conflict',
        string='Conflit',
        required=True
    )
    
    resolution_method = fields.Selection([
        ('reassign_teacher', 'Réassigner le professeur'),
        ('reassign_room', 'Réassigner la salle'),
        ('reschedule_slot', 'Reprogrammer le créneau'),
        ('split_class', 'Diviser la classe'),
        ('merge_slots', 'Fusionner les créneaux'),
        ('change_subject', 'Changer la matière'),
        ('manual_fix', 'Correction manuelle'),
    ], string='Méthode de résolution', required=True)
    
    slot_to_modify = fields.Many2one(
        'edu.schedule.slot',
        string='Créneau à modifier'
    )
    
    new_teacher_id = fields.Many2one(
        'op.faculty',
        string='Nouveau professeur'
    )
    
    new_room_id = fields.Many2one(
        'edu.room.enhanced',
        string='Nouvelle salle'
    )
    
    new_date = fields.Date(
        string='Nouvelle date'
    )
    
    new_start_time = fields.Float(
        string='Nouvelle heure de début'
    )
    
    new_end_time = fields.Float(
        string='Nouvelle heure de fin'
    )
    
    notes = fields.Text(
        string='Notes de résolution'
    )
    
    def action_apply_resolution(self):
        """Appliquer la résolution choisie"""
        self.ensure_one()
        
        try:
            success = False
            
            if self.resolution_method == 'reassign_teacher':
                success = self._reassign_teacher()
            elif self.resolution_method == 'reassign_room':
                success = self._reassign_room()
            elif self.resolution_method == 'reschedule_slot':
                success = self._reschedule_slot()
            elif self.resolution_method == 'manual_fix':
                success = self._manual_fix()
            
            if success:
                # Marquer le conflit comme résolu
                self.conflict_id.write({
                    'state': 'resolved',
                    'resolution_method': 'manual',
                    'resolution_notes': self.notes,
                    'resolved_date': fields.Datetime.now(),
                    'resolved_by': self.env.user.id,
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Conflit résolu'),
                        'message': _('Le conflit a été résolu avec succès.'),
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Impossible d\'appliquer cette résolution.'))
                
        except Exception as e:
            raise UserError(_('Erreur lors de la résolution: %s') % str(e))
    
    def _reassign_teacher(self):
        """Réassigner le professeur"""
        if not self.slot_to_modify or not self.new_teacher_id:
            return False
        
        self.slot_to_modify.write({'teacher_id': self.new_teacher_id.id})
        return True
    
    def _reassign_room(self):
        """Réassigner la salle"""
        if not self.slot_to_modify or not self.new_room_id:
            return False
        
        self.slot_to_modify.write({'room_id': self.new_room_id.id})
        return True
    
    def _reschedule_slot(self):
        """Reprogrammer le créneau"""
        if not self.slot_to_modify:
            return False
        
        update_vals = {}
        
        if self.new_date:
            update_vals['date'] = self.new_date
        
        if self.new_start_time:
            update_vals['start_time'] = self.new_start_time
        
        if self.new_end_time:
            update_vals['end_time'] = self.new_end_time
        
        if update_vals:
            self.slot_to_modify.write(update_vals)
            return True
        
        return False
    
    def _manual_fix(self):
        """Correction manuelle - marquer simplement comme résolu"""
        return True
