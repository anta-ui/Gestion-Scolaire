# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, time

class ScheduleSlot(models.Model):
    _name = 'edu.schedule.slot'
    _description = 'Créneau horaire'
    _inherit = ['mail.thread']
    _order = 'date, start_time'

    # Relations principales
    timetable_id = fields.Many2one(
        'edu.timetable.enhanced',
        string='Emploi du temps',
        required=True,
        ondelete='cascade'
    )
    
    # Informations temporelles
    date = fields.Date(
        string='Date',
        required=True,
        tracking=True
    )
    
    start_time = fields.Float(
        string='Heure de début',
        required=True,
        help='Heure au format 24h (ex: 14.5 pour 14h30)'
    )
    
    end_time = fields.Float(
        string='Heure de fin',
        required=True,
        help='Heure au format 24h (ex: 15.5 pour 15h30)'
    )
    
    duration = fields.Float(
        string='Durée (minutes)',
        compute='_compute_duration',
        store=True
    )
    
    day_of_week = fields.Selection([
        ('0', 'Lundi'),
        ('1', 'Mardi'),
        ('2', 'Mercredi'),
        ('3', 'Jeudi'),
        ('4', 'Vendredi'),
        ('5', 'Samedi'),
        ('6', 'Dimanche'),
    ], string='Jour de la semaine', compute='_compute_day_of_week', store=True)
    
    slot_number = fields.Integer(
        string='Numéro du créneau',
        help='Numéro d\'ordre du créneau dans la journée'
    )
    
    # Contenu pédagogique
    subject_id = fields.Many2one(
        'op.subject',
        string='Matière',
        tracking=True
    )
    
    teacher_id = fields.Many2one(
        'op.faculty',
        string='Professeur',
        tracking=True
    )
    
    class_id = fields.Many2one(
        'op.batch',
        string='Classe',
        tracking=True
    )
    
    room_id = fields.Many2one(
        'edu.room.enhanced',
        string='Salle',
        tracking=True
    )
    
    # Informations complémentaires
    lesson_type = fields.Selection([
        ('lecture', 'Cours magistral'),
        ('tutorial', 'TD'),
        ('practical', 'TP'),
        ('exam', 'Examen'),
        ('evaluation', 'Évaluation'),
        ('conference', 'Conférence'),
        ('other', 'Autre'),
    ], string='Type de cours', default='lecture')
    
    notes = fields.Text(
        string='Notes',
        help='Notes spécifiques pour ce créneau'
    )
    
    # États et statuts
    state = fields.Selection([
        ('scheduled', 'Programmé'),
        ('confirmed', 'Confirmé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('rescheduled', 'Reprogrammé'),
    ], string='État', default='scheduled', tracking=True)
    
    is_mandatory = fields.Boolean(
        string='Obligatoire',
        default=True,
        help='Ce créneau est-il obligatoire pour les étudiants?'
    )
    
    is_locked = fields.Boolean(
        string='Verrouillé',
        default=False,
        help='Empêche la modification par l\'optimiseur IA'
    )
    
    # Capacité et inscriptions
    capacity = fields.Integer(
        string='Capacité',
        compute='_compute_capacity'
    )
    
    enrolled_count = fields.Integer(
        string='Inscrits',
        compute='_compute_enrolled_count'
    )
    
    attendance_rate = fields.Float(
        string='Taux de présence (%)',
        compute='_compute_attendance_rate'
    )
    
    # Métadonnées
    color = fields.Integer(
        string='Couleur',
        help='Couleur pour l\'affichage calendrier'
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10
    )
    
    active = fields.Boolean(
        default=True
    )
    
    # Champs calculés pour l'affichage
    display_name_custom = fields.Char(
        string='Nom d\'affichage',
        compute='_compute_display_name_custom'
    )
    
    time_range = fields.Char(
        string='Horaire',
        compute='_compute_time_range'
    )
    
    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Calculer la durée en minutes"""
        for record in self:
            if record.start_time and record.end_time:
                record.duration = (record.end_time - record.start_time) * 60
            else:
                record.duration = 0
    
    @api.depends('date')
    def _compute_day_of_week(self):
        """Calculer le jour de la semaine"""
        for record in self:
            if record.date:
                record.day_of_week = str(record.date.weekday())
            else:
                record.day_of_week = False
    
    @api.depends('room_id', 'class_id')
    def _compute_capacity(self):
        """Calculer la capacité du créneau"""
        for record in self:
            if record.room_id:
                record.capacity = record.room_id.capacity
            elif record.class_id:
                record.capacity = len(record.class_id.student_ids)
            else:
                record.capacity = 0
    
    def _compute_enrolled_count(self):
        """Calculer le nombre d'inscrits"""
        for record in self:
            if record.class_id:
                record.enrolled_count = len(record.class_id.student_ids)
            else:
                record.enrolled_count = 0
    
    def _compute_attendance_rate(self):
        """Calculer le taux de présence"""
        for record in self:
            # TODO: Intégrer avec le module de présences
            record.attendance_rate = 0.0
    
    @api.depends('subject_id', 'teacher_id', 'class_id', 'room_id')
    def _compute_display_name_custom(self):
        """Générer le nom d'affichage personnalisé"""
        for record in self:
            parts = []
            if record.subject_id:
                parts.append(record.subject_id.name)
            if record.teacher_id:
                parts.append(f"({record.teacher_id.name})")
            if record.class_id:
                parts.append(f"- {record.class_id.name}")
            if record.room_id:
                parts.append(f"[{record.room_id.name}]")
            
            record.display_name_custom = " ".join(parts) if parts else _('Créneau libre')
    
    @api.depends('start_time', 'end_time')
    def _compute_time_range(self):
        """Formater l'horaire pour l'affichage"""
        for record in self:
            if record.start_time and record.end_time:
                start_h = int(record.start_time)
                start_m = int((record.start_time - start_h) * 60)
                end_h = int(record.end_time)
                end_m = int((record.end_time - end_h) * 60)
                
                record.time_range = f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
            else:
                record.time_range = ""
    
    @api.constrains('start_time', 'end_time')
    def _check_time_validity(self):
        """Valider les heures"""
        for record in self:
            if record.start_time >= record.end_time:
                raise ValidationError(_('L\'heure de fin doit être postérieure à l\'heure de début.'))
            
            if record.start_time < 0 or record.start_time > 24:
                raise ValidationError(_('L\'heure de début doit être entre 0 et 24.'))
                
            if record.end_time < 0 or record.end_time > 24:
                raise ValidationError(_('L\'heure de fin doit être entre 0 et 24.'))
    
    @api.constrains('teacher_id', 'date', 'start_time', 'end_time')
    def _check_teacher_availability(self):
        """Vérifier la disponibilité du professeur"""
        for record in self:
            if record.teacher_id and record.date and record.start_time and record.end_time:
                # Chercher les conflits avec d'autres créneaux
                conflicting_slots = self.search([
                    ('id', '!=', record.id),
                    ('teacher_id', '=', record.teacher_id.id),
                    ('date', '=', record.date),
                    ('state', 'not in', ['cancelled', 'rescheduled']),
                    '|',
                    '&', ('start_time', '<=', record.start_time), ('end_time', '>', record.start_time),
                    '&', ('start_time', '<', record.end_time), ('end_time', '>=', record.end_time),
                ])
                
                if conflicting_slots:
                    raise ValidationError(_(
                        'Le professeur %s n\'est pas disponible à cette heure. '
                        'Conflit avec: %s'
                    ) % (record.teacher_id.name, conflicting_slots[0].display_name_custom))
    
    @api.constrains('room_id', 'date', 'start_time', 'end_time')
    def _check_room_availability(self):
        """Vérifier la disponibilité de la salle"""
        for record in self:
            if record.room_id and record.date and record.start_time and record.end_time:
                # Chercher les conflits avec d'autres créneaux
                conflicting_slots = self.search([
                    ('id', '!=', record.id),
                    ('room_id', '=', record.room_id.id),
                    ('date', '=', record.date),
                    ('state', 'not in', ['cancelled', 'rescheduled']),
                    '|',
                    '&', ('start_time', '<=', record.start_time), ('end_time', '>', record.start_time),
                    '&', ('start_time', '<', record.end_time), ('end_time', '>=', record.end_time),
                ])
                
                if conflicting_slots:
                    raise ValidationError(_(
                        'La salle %s n\'est pas disponible à cette heure. '
                        'Conflit avec: %s'
                    ) % (record.room_id.name, conflicting_slots[0].display_name_custom))
    
    def action_confirm(self):
        """Confirmer le créneau"""
        self.write({'state': 'confirmed'})
        self.message_post(body=_('Créneau confirmé'))
    
    def action_cancel(self):
        """Annuler le créneau"""
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Créneau annulé'))
        
        # Notifier les concernés
        self._notify_cancellation()
    
    def action_reschedule(self):
        """Reprogrammer le créneau"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reprogrammer le créneau'),
            'res_model': 'edu.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_slot_id': self.id,
            },
        }
    
    def action_mark_in_progress(self):
        """Marquer en cours"""
        self.write({'state': 'in_progress'})
        self.message_post(body=_('Cours commencé'))
    
    def action_mark_completed(self):
        """Marquer terminé"""
        self.write({'state': 'completed'})
        self.message_post(body=_('Cours terminé'))
    
    def _notify_cancellation(self):
        """Notifier l'annulation du créneau"""
        # Notifier le professeur
        if self.teacher_id and self.teacher_id.user_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.teacher_id.user_id.id,
                summary=_('Cours annulé'),
                note=_('Le cours "%s" du %s a été annulé.') % (
                    self.display_name_custom,
                    self.date.strftime('%d/%m/%Y')
                ),
            )
        
        # Notifier les étudiants de la classe
        if self.class_id:
            # TODO: Implémenter notification aux étudiants
            pass
    
    @api.model
    def get_calendar_events(self, start_date, end_date, timetable_id=None):
        """Récupérer les événements pour le calendrier"""
        domain = [
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', 'not in', ['cancelled']),
        ]
        
        if timetable_id:
            domain.append(('timetable_id', '=', timetable_id))
        
        slots = self.search(domain)
        events = []
        
        for slot in slots:
            # Convertir en datetime pour FullCalendar
            start_datetime = datetime.combine(
                slot.date,
                time(int(slot.start_time), int((slot.start_time % 1) * 60))
            )
            end_datetime = datetime.combine(
                slot.date,
                time(int(slot.end_time), int((slot.end_time % 1) * 60))
            )
            
            event = {
                'id': slot.id,
                'title': slot.display_name_custom,
                'start': start_datetime.isoformat(),
                'end': end_datetime.isoformat(),
                'backgroundColor': self._get_event_color(slot),
                'borderColor': self._get_event_border_color(slot),
                'textColor': '#ffffff',
                'extendedProps': {
                    'teacher': slot.teacher_id.name if slot.teacher_id else '',
                    'room': slot.room_id.name if slot.room_id else '',
                    'class': slot.class_id.name if slot.class_id else '',
                    'type': slot.lesson_type,
                    'state': slot.state,
                    'notes': slot.notes or '',
                },
            }
            events.append(event)
        
        return events
    
    def _get_event_color(self, slot):
        """Obtenir la couleur de l'événement selon le type"""
        color_map = {
            'lecture': '#3498db',      # Bleu
            'tutorial': '#2ecc71',     # Vert
            'practical': '#e74c3c',    # Rouge
            'exam': '#9b59b6',         # Violet
            'evaluation': '#f39c12',   # Orange
            'conference': '#1abc9c',   # Turquoise
            'other': '#95a5a6',        # Gris
        }
        return color_map.get(slot.lesson_type, '#95a5a6')
    
    def _get_event_border_color(self, slot):
        """Obtenir la couleur de bordure selon l'état"""
        if slot.state == 'cancelled':
            return '#e74c3c'
        elif slot.state == 'confirmed':
            return '#27ae60'
        elif slot.state == 'in_progress':
            return '#f39c12'
        elif slot.state == 'completed':
            return '#95a5a6'
        else:
            return '#3498db'
