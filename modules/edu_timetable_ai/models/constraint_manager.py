# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json

class TimetableConstraint(models.Model):
    _name = 'edu.timetable.constraint'
    _description = 'Contrainte d\'emploi du temps'
    _inherit = ['mail.thread']
    _order = 'priority desc, name'

    # Informations de base
    name = fields.Char(
        string='Nom de la contrainte',
        required=True,
        tracking=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    timetable_id = fields.Many2one(
        'edu.timetable.enhanced',
        string='Emploi du temps',
        ondelete='cascade'
    )
    
    # Type et catégorie
    constraint_type = fields.Selection([
        ('hard', 'Contrainte dure'),
        ('soft', 'Contrainte souple'),
        ('preference', 'Préférence'),
    ], string='Type', default='hard', required=True, tracking=True)
    
    category = fields.Selection([
        ('teacher', 'Professeur'),
        ('student', 'Étudiant'),
        ('room', 'Salle'),
        ('subject', 'Matière'),
        ('time', 'Horaire'),
        ('resource', 'Ressource'),
        ('global', 'Globale'),
    ], string='Catégorie', required=True, tracking=True)
    
    # Entités concernées
    teacher_ids = fields.Many2many(
        'op.faculty',
        'constraint_teacher_rel',
        'constraint_id',
        'teacher_id',
        string='Professeurs concernés'
    )
    
    student_ids = fields.Many2many(
        'op.student',
        'constraint_student_rel',
        'constraint_id',
        'student_id',
        string='Étudiants concernés'
    )
    
    class_ids = fields.Many2many(
        'op.batch',
        'constraint_class_rel',
        'constraint_id',
        'class_id',
        string='Classes concernées'
    )
    
    room_ids = fields.Many2many(
        'edu.room.enhanced',
        'constraint_room_rel',
        'constraint_id',
        'room_id',
        string='Salles concernées'
    )
    
    subject_ids = fields.Many2many(
        'op.subject',
        'constraint_subject_rel',
        'constraint_id',
        'subject_id',
        string='Matières concernées'
    )
    
    # Contraintes temporelles
    time_constraint_type = fields.Selection([
        ('no_before', 'Pas avant'),
        ('no_after', 'Pas après'),
        ('only_between', 'Seulement entre'),
        ('not_between', 'Pas entre'),
        ('specific_days', 'Jours spécifiques'),
        ('max_per_day', 'Maximum par jour'),
        ('min_gap', 'Écart minimum'),
        ('max_consecutive', 'Maximum consécutif'),
    ], string='Type de contrainte temporelle')
    
    # Heures et jours
    start_time = fields.Float(
        string='Heure de début',
        help='Heure au format 24h (ex: 14.5 pour 14h30)'
    )
    
    end_time = fields.Float(
        string='Heure de fin',
        help='Heure au format 24h (ex: 16.5 pour 16h30)'
    )
    
    allowed_days = fields.Selection([
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
        ('friday', 'Vendredi'),
        ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'),
    ], string='Jours autorisés')
    
    forbidden_days = fields.Selection([
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
        ('friday', 'Vendredi'),
        ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'),
    ], string='Jours interdits')
    
    # Contraintes de capacité et ressources
    min_capacity = fields.Integer(
        string='Capacité minimum',
        help='Capacité minimum requise pour la salle'
    )
    
    max_capacity = fields.Integer(
        string='Capacité maximum',
        help='Capacité maximum autorisée pour la salle'
    )
    
    required_equipment_ids = fields.Many2many(
        'edu.room.equipment',
        'constraint_equipment_rel',
        'constraint_id',
        'equipment_id',
        string='Équipements requis'
    )
    
    # Paramètres numériques
    max_per_day = fields.Integer(
        string='Maximum par jour',
        help='Nombre maximum de créneaux par jour'
    )
    
    min_gap_hours = fields.Float(
        string='Écart minimum (heures)',
        help='Écart minimum entre deux créneaux en heures'
    )
    
    max_consecutive = fields.Integer(
        string='Maximum consécutif',
        help='Nombre maximum de créneaux consécutifs'
    )
    
    # Priorité et poids
    priority = fields.Integer(
        string='Priorité',
        default=5,
        help='Priorité de la contrainte (1-10, 10 = priorité max)'
    )
    
    weight = fields.Float(
        string='Poids',
        default=1.0,
        help='Poids de la contrainte pour l\'optimisation'
    )
    
    # État et activation
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    is_violated = fields.Boolean(
        string='Violée',
        compute='_compute_violation_status',
        help='Cette contrainte est-elle actuellement violée?'
    )
    
    violation_count = fields.Integer(
        string='Nombre de violations',
        compute='_compute_violation_status'
    )
    
    # Configuration avancée
    custom_logic = fields.Text(
        string='Logique personnalisée',
        help='Code Python personnalisé pour des contraintes complexes'
    )
    
    parameters = fields.Text(
        string='Paramètres (JSON)',
        help='Paramètres additionnels au format JSON'
    )
    
    # Métadonnées
    created_by_ai = fields.Boolean(
        string='Créée par IA',
        default=False,
        readonly=True
    )
    
    last_check = fields.Datetime(
        string='Dernière vérification',
        readonly=True
    )
    
    @api.depends('timetable_id.schedule_line_ids')
    def _compute_violation_status(self):
        """Calculer le statut de violation de la contrainte"""
        for constraint in self:
            if constraint.timetable_id:
                violations = constraint._check_constraint_violations()
                constraint.violation_count = len(violations)
                constraint.is_violated = constraint.violation_count > 0
            else:
                constraint.violation_count = 0
                constraint.is_violated = False
    
    def _check_constraint_violations(self):
        """Vérifier les violations de cette contrainte"""
        self.ensure_one()
        violations = []
        
        if not self.timetable_id:
            return violations
        
        slots = self.timetable_id.schedule_line_ids.filtered(lambda x: x.state not in ['cancelled'])
        
        # Vérifications selon le type de contrainte
        if self.time_constraint_type == 'no_before':
            violations.extend(self._check_no_before_violations(slots))
        elif self.time_constraint_type == 'no_after':
            violations.extend(self._check_no_after_violations(slots))
        elif self.time_constraint_type == 'only_between':
            violations.extend(self._check_only_between_violations(slots))
        elif self.time_constraint_type == 'not_between':
            violations.extend(self._check_not_between_violations(slots))
        elif self.time_constraint_type == 'max_per_day':
            violations.extend(self._check_max_per_day_violations(slots))
        elif self.time_constraint_type == 'min_gap':
            violations.extend(self._check_min_gap_violations(slots))
        elif self.time_constraint_type == 'max_consecutive':
            violations.extend(self._check_max_consecutive_violations(slots))
        
        # Vérifications de capacité
        if self.min_capacity or self.max_capacity:
            violations.extend(self._check_capacity_violations(slots))
        
        # Vérifications d'équipement
        if self.required_equipment_ids:
            violations.extend(self._check_equipment_violations(slots))
        
        return violations
    
    def _check_no_before_violations(self, slots):
        """Vérifier les violations 'pas avant'"""
        violations = []
        if not self.start_time:
            return violations
        
        filtered_slots = self._filter_slots_by_entities(slots)
        
        for slot in filtered_slots:
            if slot.start_time < self.start_time:
                violations.append({
                    'slot_id': slot.id,
                    'message': _('Créneau programmé avant %s') % self._format_time(self.start_time),
                })
        
        return violations
    
    def _check_no_after_violations(self, slots):
        """Vérifier les violations 'pas après'"""
        violations = []
        if not self.end_time:
            return violations
        
        filtered_slots = self._filter_slots_by_entities(slots)
        
        for slot in filtered_slots:
            if slot.end_time > self.end_time:
                violations.append({
                    'slot_id': slot.id,
                    'message': _('Créneau programmé après %s') % self._format_time(self.end_time),
                })
        
        return violations
    
    def _check_only_between_violations(self, slots):
        """Vérifier les violations 'seulement entre'"""
        violations = []
        if not (self.start_time and self.end_time):
            return violations
        
        filtered_slots = self._filter_slots_by_entities(slots)
        
        for slot in filtered_slots:
            if not (self.start_time <= slot.start_time and slot.end_time <= self.end_time):
                violations.append({
                    'slot_id': slot.id,
                    'message': _('Créneau en dehors de la plage %s - %s') % (
                        self._format_time(self.start_time),
                        self._format_time(self.end_time)
                    ),
                })
        
        return violations
    
    def _check_max_per_day_violations(self, slots):
        """Vérifier les violations 'maximum par jour'"""
        violations = []
        if not self.max_per_day:
            return violations
        
        filtered_slots = self._filter_slots_by_entities(slots)
        
        # Grouper par date
        slots_by_date = {}
        for slot in filtered_slots:
            date = slot.date
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(slot)
        
        # Vérifier chaque jour
        for date, day_slots in slots_by_date.items():
            if len(day_slots) > self.max_per_day:
                for slot in day_slots[self.max_per_day:]:
                    violations.append({
                        'slot_id': slot.id,
                        'message': _('Dépassement du maximum %d créneaux par jour') % self.max_per_day,
                    })
        
        return violations
    
    def _check_min_gap_violations(self, slots):
        """Vérifier les violations 'écart minimum'"""
        violations = []
        if not self.min_gap_hours:
            return violations
        
        filtered_slots = self._filter_slots_by_entities(slots)
        
        # Grouper par entité et par date
        entity_slots = self._group_slots_by_entity_and_date(filtered_slots)
        
        for entity_date_slots in entity_slots.values():
            for date_slots in entity_date_slots.values():
                # Trier par heure de début
                sorted_slots = sorted(date_slots, key=lambda x: x.start_time)
                
                for i in range(len(sorted_slots) - 1):
                    current_slot = sorted_slots[i]
                    next_slot = sorted_slots[i + 1]
                    
                    gap = next_slot.start_time - current_slot.end_time
                    if gap < self.min_gap_hours:
                        violations.append({
                            'slot_id': next_slot.id,
                            'message': _('Écart insuffisant avec le créneau précédent (%.1fh < %.1fh)') % (
                                gap, self.min_gap_hours
                            ),
                        })
        
        return violations
    
    def _check_capacity_violations(self, slots):
        """Vérifier les violations de capacité"""
        violations = []
        filtered_slots = self._filter_slots_by_entities(slots)
        
        for slot in filtered_slots:
            if slot.room_id:
                room_capacity = slot.room_id.capacity
                
                if self.min_capacity and room_capacity < self.min_capacity:
                    violations.append({
                        'slot_id': slot.id,
                        'message': _('Capacité salle insuffisante (%d < %d)') % (
                            room_capacity, self.min_capacity
                        ),
                    })
                
                if self.max_capacity and room_capacity > self.max_capacity:
                    violations.append({
                        'slot_id': slot.id,
                        'message': _('Capacité salle excessive (%d > %d)') % (
                            room_capacity, self.max_capacity
                        ),
                    })
        
        return violations
    
    def _check_equipment_violations(self, slots):
        """Vérifier les violations d'équipement"""
        violations = []
        filtered_slots = self._filter_slots_by_entities(slots)
        
        for slot in filtered_slots:
            if slot.room_id:
                room_equipment = slot.room_id.equipment_ids
                missing_equipment = self.required_equipment_ids - room_equipment
                
                if missing_equipment:
                    violations.append({
                        'slot_id': slot.id,
                        'message': _('Équipements manquants: %s') % (
                            ', '.join(missing_equipment.mapped('name'))
                        ),
                    })
        
        return violations
    
    def _filter_slots_by_entities(self, slots):
        """Filtrer les créneaux selon les entités concernées"""
        filtered_slots = slots
        
        # Filtrer par professeurs
        if self.teacher_ids:
            filtered_slots = filtered_slots.filtered(
                lambda x: x.teacher_id in self.teacher_ids
            )
        
        # Filtrer par classes
        if self.class_ids:
            filtered_slots = filtered_slots.filtered(
                lambda x: x.class_id in self.class_ids
            )
        
        # Filtrer par salles
        if self.room_ids:
            filtered_slots = filtered_slots.filtered(
                lambda x: x.room_id in self.room_ids
            )
        
        # Filtrer par matières
        if self.subject_ids:
            filtered_slots = filtered_slots.filtered(
                lambda x: x.subject_id in self.subject_ids
            )
        
        return filtered_slots
    
    def _group_slots_by_entity_and_date(self, slots):
        """Grouper les créneaux par entité et par date"""
        groups = {}
        
        for slot in slots:
            # Déterminer l'entité principale
            entity_key = None
            
            if self.category == 'teacher' and slot.teacher_id:
                entity_key = f"teacher_{slot.teacher_id.id}"
            elif self.category == 'student' and slot.class_id:
                entity_key = f"class_{slot.class_id.id}"
            elif self.category == 'room' and slot.room_id:
                entity_key = f"room_{slot.room_id.id}"
            elif self.category == 'subject' and slot.subject_id:
                entity_key = f"subject_{slot.subject_id.id}"
            else:
                entity_key = "global"
            
            if entity_key not in groups:
                groups[entity_key] = {}
            
            date = slot.date
            if date not in groups[entity_key]:
                groups[entity_key][date] = []
            
            groups[entity_key][date].append(slot)
        
        return groups
    
    def _format_time(self, time_float):
        """Formater l'heure pour l'affichage"""
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
    
    def action_check_violations(self):
        """Forcer la vérification des violations"""
        self.ensure_one()
        violations = self._check_constraint_violations()
        
        self.write({
            'last_check': fields.Datetime.now(),
        })
        
        if violations:
            message = _('Contrainte violée: %d violations détectées') % len(violations)
            self.message_post(body=message)
        else:
            message = _('Contrainte respectée: aucune violation détectée')
            self.message_post(body=message)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Vérification terminée'),
                'message': message,
                'type': 'success' if not violations else 'warning',
            }
        }
    
    @api.model
    def create_ai_constraints(self, timetable_id):
        """Créer des contraintes automatiques basées sur l'IA"""
        constraints_data = [
            {
                'name': _('Pas de cours avant 8h'),
                'timetable_id': timetable_id,
                'constraint_type': 'hard',
                'category': 'time',
                'time_constraint_type': 'no_before',
                'start_time': 8.0,
                'priority': 9,
                'created_by_ai': True,
            },
            {
                'name': _('Pas de cours après 18h'),
                'timetable_id': timetable_id,
                'constraint_type': 'hard',
                'category': 'time',
                'time_constraint_type': 'no_after',
                'end_time': 18.0,
                'priority': 8,
                'created_by_ai': True,
            },
            {
                'name': _('Maximum 6 créneaux par jour'),
                'timetable_id': timetable_id,
                'constraint_type': 'soft',
                'category': 'teacher',
                'time_constraint_type': 'max_per_day',
                'max_per_day': 6,
                'priority': 6,
                'created_by_ai': True,
            },
            {
                'name': _('Pause minimum 15 minutes'),
                'timetable_id': timetable_id,
                'constraint_type': 'soft',
                'category': 'teacher',
                'time_constraint_type': 'min_gap',
                'min_gap_hours': 0.25,
                'priority': 5,
                'created_by_ai': True,
            },
        ]
        
        created_constraints = []
        for constraint_data in constraints_data:
            constraint = self.create(constraint_data)
            created_constraints.append(constraint)
        
        return created_constraints
