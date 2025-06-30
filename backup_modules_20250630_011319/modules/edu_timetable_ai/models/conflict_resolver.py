# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class TimetableConflict(models.Model):
    _name = 'edu.timetable.conflict'
    _description = 'Conflit d\'emploi du temps'
    _order = 'severity desc, create_date desc'

    # Informations de base
    name = fields.Char(string='Nom du conflit', compute='_compute_name', store=True)
    
    timetable_id = fields.Many2one(
        'edu.timetable.enhanced',
        string='Emploi du temps',
        required=True,
        ondelete='cascade'
    )
    
    conflict_type = fields.Selection([
        ('teacher_conflict', 'Conflit professeur'),
        ('room_conflict', 'Conflit de salle'),
        ('class_conflict', 'Conflit de classe'),
        ('capacity_conflict', 'Problème de capacité'),
        ('equipment_conflict', 'Conflit d\'équipement'),
        ('constraint_violation', 'Violation de contrainte'),
    ], string='Type de conflit', required=True)
    
    severity = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    ], string='Sévérité', required=True, default='medium')
    
    state = fields.Selection([
        ('active', 'Actif'),
        ('resolved', 'Résolu'),
        ('ignored', 'Ignoré'),
    ], string='État', default='active')
    
    # Description du conflit
    title = fields.Char(string='Titre', required=True)
    description = fields.Text(string='Description')
    
    # Relations avec les créneaux concernés
    slot_ids = fields.Many2many(
        'edu.schedule.slot',
        string='Créneaux concernés'
    )
    
    # Entité concernée
    entity_type = fields.Selection([
        ('teacher', 'Professeur'),
        ('room', 'Salle'),
        ('class', 'Classe'),
        ('capacity', 'Capacité'),
        ('equipment', 'Équipement'),
    ], string='Type d\'entité')
    
    entity_id = fields.Integer(string='ID de l\'entité')
    entity_name = fields.Char(string='Nom de l\'entité', compute='_compute_entity_name')
    
    # Actions suggérées
    suggested_actions = fields.Text(
        string='Actions suggérées (JSON)',
        help='Liste des actions suggérées au format JSON'
    )
    
    # Résolution
    resolution_notes = fields.Text(string='Notes de résolution')
    resolved_date = fields.Datetime(string='Date de résolution')
    resolved_by = fields.Many2one('res.users', string='Résolu par')
    
    # Métadonnées
    auto_resolvable = fields.Boolean(
        string='Résolution automatique possible',
        default=False
    )
    
    @api.depends('conflict_type', 'title')
    def _compute_name(self):
        for record in self:
            if record.title:
                record.name = record.title
            else:
                record.name = dict(record._fields['conflict_type'].selection).get(record.conflict_type, 'Conflit')
    
    @api.depends('entity_type', 'entity_id')
    def _compute_entity_name(self):
        """Calculer le nom de l'entité concernée"""
        for record in self:
            if record.entity_type and record.entity_id:
                if record.entity_type == 'teacher':
                    teacher = self.env['op.faculty'].browse(record.entity_id)
                    record.entity_name = teacher.name if teacher.exists() else 'Professeur inconnu'
                elif record.entity_type == 'room':
                    room = self.env['edu.room.enhanced'].browse(record.entity_id)
                    record.entity_name = room.name if room.exists() else 'Salle inconnue'
                elif record.entity_type == 'class':
                    class_obj = self.env['op.batch'].browse(record.entity_id)
                    record.entity_name = class_obj.name if class_obj.exists() else 'Classe inconnue'
                else:
                    entity_type = dict(record._fields['entity_type'].selection).get(record.entity_type, 'Entité')
                    record.entity_name = f"{entity_type} {record.entity_id}"
            else:
                record.entity_name = 'Entité non spécifiée'
    
    def action_resolve(self):
        """Marquer le conflit comme résolu"""
        self.ensure_one()
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now(),
            'resolved_by': self.env.user.id,
        })
    
    def action_ignore(self):
        """Ignorer le conflit"""
        self.ensure_one()
        self.write({
            'state': 'ignored',
        })
    
    def action_auto_resolve(self):
        """Tenter une résolution automatique"""
        self.ensure_one()
        if not self.auto_resolvable:
            return False
        
        resolver = self.env['edu.conflict.resolver']
        conflict_data = {
            'type': self.conflict_type,
            'slot_ids': self.slot_ids.ids,
            'suggested_actions': self.suggested_actions,
        }
        
        success = resolver.resolve_conflict_auto(conflict_data)
        if success:
            self.action_resolve()
        
        return success

class ConflictResolver(models.Model):
    _name = 'edu.conflict.resolver'
    _description = 'Résolveur de conflits d\'emploi du temps'

    @api.model
    def detect_conflicts(self, timetable):
        """Détecter tous les conflits dans un emploi du temps"""
        conflicts = []
        
        # Récupérer tous les créneaux actifs
        slots = timetable.schedule_line_ids.filtered(
            lambda x: x.state not in ['cancelled', 'rescheduled']
        )
        
        # Détecter les différents types de conflits
        conflicts.extend(self._detect_teacher_conflicts(slots))
        conflicts.extend(self._detect_room_conflicts(slots))
        conflicts.extend(self._detect_class_conflicts(slots))
        conflicts.extend(self._detect_capacity_conflicts(slots))
        conflicts.extend(self._detect_equipment_conflicts(slots))
        
        return conflicts
    
    def _detect_teacher_conflicts(self, slots):
        """Détecter les conflits de professeurs"""
        conflicts = []
        teacher_slots = {}
        
        # Grouper les créneaux par professeur
        for slot in slots.filtered(lambda x: x.teacher_id):
            teacher_id = slot.teacher_id.id
            if teacher_id not in teacher_slots:
                teacher_slots[teacher_id] = []
            teacher_slots[teacher_id].append(slot)
        
        # Vérifier les conflits pour chaque professeur
        for teacher_id, teacher_slot_list in teacher_slots.items():
            for i, slot1 in enumerate(teacher_slot_list):
                for slot2 in teacher_slot_list[i+1:]:
                    if self._slots_overlap(slot1, slot2):
                        conflicts.append({
                            'type': 'teacher_conflict',
                            'severity': 'high',
                            'title': _('Conflit professeur'),
                            'description': _(
                                'Le professeur %s est assigné à deux créneaux simultanés'
                            ) % slot1.teacher_id.name,
                            'slot_ids': [slot1.id, slot2.id],
                            'entity_type': 'teacher',
                            'entity_id': teacher_id,
                            'suggested_actions': [
                                'reassign_teacher',
                                'reschedule_slot',
                                'split_class'
                            ]
                        })
        
        return conflicts
    
    def _detect_room_conflicts(self, slots):
        """Détecter les conflits de salles"""
        conflicts = []
        room_slots = {}
        
        # Grouper les créneaux par salle
        for slot in slots.filtered(lambda x: x.room_id):
            room_id = slot.room_id.id
            if room_id not in room_slots:
                room_slots[room_id] = []
            room_slots[room_id].append(slot)
        
        # Vérifier les conflits pour chaque salle
        for room_id, room_slot_list in room_slots.items():
            for i, slot1 in enumerate(room_slot_list):
                for slot2 in room_slot_list[i+1:]:
                    if self._slots_overlap(slot1, slot2):
                        conflicts.append({
                            'type': 'room_conflict',
                            'severity': 'high',
                            'title': _('Conflit de salle'),
                            'description': _(
                                'La salle %s est réservée pour deux créneaux simultanés'
                            ) % slot1.room_id.name,
                            'slot_ids': [slot1.id, slot2.id],
                            'entity_type': 'room',
                            'entity_id': room_id,
                            'suggested_actions': [
                                'reassign_room',
                                'reschedule_slot',
                                'find_alternative_room'
                            ]
                        })
        
        return conflicts
    
    def _detect_class_conflicts(self, slots):
        """Détecter les conflits de classes"""
        conflicts = []
        class_slots = {}
        
        # Grouper les créneaux par classe
        for slot in slots.filtered(lambda x: x.class_id):
            class_id = slot.class_id.id
            if class_id not in class_slots:
                class_slots[class_id] = []
            class_slots[class_id].append(slot)
        
        # Vérifier les conflits pour chaque classe
        for class_id, class_slot_list in class_slots.items():
            for i, slot1 in enumerate(class_slot_list):
                for slot2 in class_slot_list[i+1:]:
                    if self._slots_overlap(slot1, slot2):
                        conflicts.append({
                            'type': 'class_conflict',
                            'severity': 'high',
                            'title': _('Conflit de classe'),
                            'description': _(
                                'La classe %s a deux cours simultanés'
                            ) % slot1.class_id.name,
                            'slot_ids': [slot1.id, slot2.id],
                            'entity_type': 'class',
                            'entity_id': class_id,
                            'suggested_actions': [
                                'reschedule_slot',
                                'merge_classes',
                                'split_subject'
                            ]
                        })
        
        return conflicts
    
    def _detect_capacity_conflicts(self, slots):
        """Détecter les conflits de capacité"""
        conflicts = []
        
        for slot in slots.filtered(lambda x: x.room_id and x.class_id):
            room_capacity = slot.room_id.capacity
            class_size = len(slot.class_id.student_ids)
            
            if class_size > room_capacity:
                conflicts.append({
                    'type': 'capacity_conflict',
                    'severity': 'medium',
                    'title': _('Problème de capacité'),
                    'description': _(
                        'La salle %s (capacité: %d) est trop petite pour la classe %s (%d étudiants)'
                    ) % (slot.room_id.name, room_capacity, slot.class_id.name, class_size),
                    'slot_ids': [slot.id],
                    'entity_type': 'capacity',
                    'entity_id': slot.room_id.id,
                    'suggested_actions': [
                        'find_larger_room',
                        'split_class',
                        'use_overflow_room'
                    ]
                })
        
        return conflicts
    
    def _detect_equipment_conflicts(self, slots):
        """Détecter les conflits d'équipement"""
        conflicts = []
        
        for slot in slots.filtered(lambda x: x.room_id and x.subject_id):
            # Vérifier si la matière nécessite des équipements spécifiques
            # TODO: Implémenter la logique d'équipement requis
            pass
        
        return conflicts
    
    def _slots_overlap(self, slot1, slot2):
        """Vérifier si deux créneaux se chevauchent"""
        if slot1.date != slot2.date:
            return False
        
        # Vérifier le chevauchement temporel
        start1, end1 = slot1.start_time, slot1.end_time
        start2, end2 = slot2.start_time, slot2.end_time
        
        return not (end1 <= start2 or end2 <= start1)
    
    @api.model
    def resolve_conflict_auto(self, conflict_data):
        """Résoudre automatiquement un conflit"""
        conflict_type = conflict_data.get('type')
        slot_ids = conflict_data.get('slot_ids', [])
        suggested_actions = conflict_data.get('suggested_actions', [])
        
        if not slot_ids or not suggested_actions:
            return False
        
        slots = self.env['edu.schedule.slot'].browse(slot_ids)
        
        # Essayer les actions suggérées dans l'ordre
        for action in suggested_actions:
            try:
                if action == 'reassign_teacher':
                    success = self._reassign_teacher(slots)
                elif action == 'reassign_room':
                    success = self._reassign_room(slots)
                elif action == 'reschedule_slot':
                    success = self._reschedule_slot(slots)
                elif action == 'find_alternative_room':
                    success = self._find_alternative_room(slots)
                elif action == 'find_larger_room':
                    success = self._find_larger_room(slots)
                else:
                    continue
                
                if success:
                    _logger.info(f'Conflit résolu automatiquement avec l\'action: {action}')
                    return True
                    
            except Exception as e:
                _logger.warning(f'Échec de résolution automatique avec {action}: {e}')
                continue
        
        return False
    
    def _reassign_teacher(self, slots):
        """Réassigner un professeur pour résoudre un conflit"""
        if len(slots) < 2:
            return False
        
        # Prendre le créneau avec la priorité la plus faible
        slot_to_reassign = min(slots, key=lambda x: x.timetable_id.priority if hasattr(x.timetable_id, 'priority') else 5)
        
        # Trouver un professeur disponible
        if not slot_to_reassign.subject_id:
            return False
        
        # Chercher des professeurs qui enseignent cette matière
        available_teachers = self.env['op.faculty'].search([
            ('subject_ids', 'in', [slot_to_reassign.subject_id.id]),
            ('active', '=', True),
        ])
        
        for teacher in available_teachers:
            if self._is_teacher_available(teacher, slot_to_reassign):
                slot_to_reassign.write({'teacher_id': teacher.id})
                return True
        
        return False
    
    def _reassign_room(self, slots):
        """Réassigner une salle pour résoudre un conflit"""
        if len(slots) < 2:
            return False
        
        # Prendre le créneau avec la priorité la plus faible
        slot_to_reassign = min(slots, key=lambda x: x.timetable_id.priority if hasattr(x.timetable_id, 'priority') else 5)
        
        # Chercher une salle disponible
        required_capacity = len(slot_to_reassign.class_id.student_ids) if slot_to_reassign.class_id else 30
        
        available_rooms = self.env['edu.room.enhanced'].search([
            ('capacity', '>=', required_capacity),
            ('is_bookable', '=', True),
            ('state', '=', 'available'),
        ])
        
        for room in available_rooms:
            if self._is_room_available(room, slot_to_reassign):
                slot_to_reassign.write({'room_id': room.id})
                return True
        
        return False
    
    def _reschedule_slot(self, slots):
        """Reprogrammer un créneau"""
        if not slots:
            return False
        
        # Prendre le créneau avec la priorité la plus faible
        slot_to_reschedule = min(slots, key=lambda x: x.timetable_id.priority if hasattr(x.timetable_id, 'priority') else 5)
        
        # Chercher un créneau libre dans la même semaine
        timetable = slot_to_reschedule.timetable_id
        current_date = slot_to_reschedule.date
        
        # Chercher dans les 7 jours suivants
        for i in range(1, 8):
            new_date = current_date + timedelta(days=i)
            
            if new_date > timetable.end_date:
                break
            
            # Chercher un créneau libre à cette date
            free_slots = self._find_free_slots(timetable, new_date)
            
            if free_slots:
                # Prendre le premier créneau libre
                free_slot = free_slots[0]
                
                # Transférer les informations
                slot_to_reschedule.write({
                    'date': new_date,
                    'start_time': free_slot['start_time'],
                    'end_time': free_slot['end_time'],
                })
                
                return True
        
        return False
    
    def _find_alternative_room(self, slots):
        """Trouver une salle alternative"""
        return self._reassign_room(slots)
    
    def _find_larger_room(self, slots):
        """Trouver une salle plus grande"""
        if not slots:
            return False
        
        slot = slots[0]
        if not slot.class_id:
            return False
        
        required_capacity = len(slot.class_id.student_ids)
        current_capacity = slot.room_id.capacity if slot.room_id else 0
        
        # Chercher une salle plus grande
        larger_rooms = self.env['edu.room.enhanced'].search([
            ('capacity', '>', max(required_capacity, current_capacity)),
            ('is_bookable', '=', True),
            ('state', '=', 'available'),
        ])
        
        for room in larger_rooms:
            if self._is_room_available(room, slot):
                slot.write({'room_id': room.id})
                return True
        
        return False
    
    def _is_teacher_available(self, teacher, slot):
        """Vérifier si un professeur est disponible"""
        conflicting_slots = self.env['edu.schedule.slot'].search([
            ('teacher_id', '=', teacher.id),
            ('date', '=', slot.date),
            ('id', '!=', slot.id),
            ('state', 'not in', ['cancelled', 'rescheduled']),
            '|',
            '&', ('start_time', '<=', slot.start_time), ('end_time', '>', slot.start_time),
            '&', ('start_time', '<', slot.end_time), ('end_time', '>=', slot.end_time),
        ])
        
        return len(conflicting_slots) == 0
    
    def _is_room_available(self, room, slot):
        """Vérifier si une salle est disponible"""
        conflicting_slots = self.env['edu.schedule.slot'].search([
            ('room_id', '=', room.id),
            ('date', '=', slot.date),
            ('id', '!=', slot.id),
            ('state', 'not in', ['cancelled', 'rescheduled']),
            '|',
            '&', ('start_time', '<=', slot.start_time), ('end_time', '>', slot.start_time),
            '&', ('start_time', '<', slot.end_time), ('end_time', '>=', slot.end_time),
        ])
        
        return len(conflicting_slots) == 0
    
    def _find_free_slots(self, timetable, date):
        """Trouver les créneaux libres pour une date"""
        # Récupérer tous les créneaux existants pour cette date
        existing_slots = self.env['edu.schedule.slot'].search([
            ('timetable_id', '=', timetable.id),
            ('date', '=', date),
            ('state', 'not in', ['cancelled']),
        ])
        
        # Générer tous les créneaux possibles pour cette date
        free_slots = []
        current_time = timetable.daily_hours_start
        
        while current_time < timetable.daily_hours_end:
            end_time = current_time + (timetable.slot_duration / 60.0)
            
            if end_time <= timetable.daily_hours_end:
                # Vérifier si ce créneau est libre
                is_free = True
                
                for existing_slot in existing_slots:
                    if not (end_time <= existing_slot.start_time or current_time >= existing_slot.end_time):
                        is_free = False
                        break
                
                if is_free:
                    free_slots.append({
                        'start_time': current_time,
                        'end_time': end_time,
                    })
            
            current_time = end_time
