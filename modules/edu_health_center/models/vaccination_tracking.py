# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class VaccinationType(models.Model):
    """Types de vaccins"""
    _name = 'vaccination.type'
    _description = 'Type de Vaccination'
    _order = 'name'

    name = fields.Char(
        string='Nom du vaccin',
        required=True,
        help="Nom du vaccin (ex: DTPolio, ROR, etc.)"
    )
    
    description = fields.Text(
        string='Description',
        help="Description détaillée du vaccin"
    )
    
    mandatory = fields.Boolean(
        string='Obligatoire',
        default=False,
        help="Ce vaccin est-il obligatoire pour la scolarisation?"
    )
    
    age_minimum = fields.Integer(
        string='Âge minimum (mois)',
        default=0,
        help="Âge minimum pour recevoir ce vaccin"
    )
    
    age_maximum = fields.Integer(
        string='Âge maximum (mois)',
        help="Âge maximum pour recevoir ce vaccin (optionnel)"
    )
    
    doses_required = fields.Integer(
        string='Nombre de doses',
        default=1,
        help="Nombre de doses requises pour ce vaccin"
    )
    
    interval_between_doses = fields.Integer(
        string='Intervalle entre doses (jours)',
        default=30,
        help="Intervalle minimum entre les doses"
    )
    
    booster_required = fields.Boolean(
        string='Rappel nécessaire',
        default=False,
        help="Ce vaccin nécessite-t-il des rappels?"
    )
    
    booster_interval = fields.Integer(
        string='Intervalle rappel (années)',
        default=10,
        help="Intervalle pour les rappels en années"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )


class VaccinationRecord(models.Model):
    """Enregistrements de vaccination"""
    _name = 'vaccination.record'
    _description = 'Enregistrement de Vaccination'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'vaccination_date desc'

    name = fields.Char(
        string='Numéro d\'enregistrement',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau'),
        help="Numéro unique de l'enregistrement"
    )
    
    # Relations
    student_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True,
        tracking=True,
        help="Étudiant vacciné"
    )
    
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        help="Dossier médical lié"
    )
    
    vaccination_type_id = fields.Many2one(
        'vaccination.type',
        string='Type de vaccin',
        required=True,
        help="Type de vaccin administré"
    )
    
    # Détails de la vaccination
    vaccination_date = fields.Date(
        string='Date de vaccination',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date d'administration du vaccin"
    )
    
    dose_number = fields.Integer(
        string='Numéro de dose',
        required=True,
        default=1,
        help="Numéro de la dose (1, 2, 3, etc.)"
    )
    
    batch_number = fields.Char(
        string='Numéro de lot',
        help="Numéro de lot du vaccin"
    )
    
    expiry_date = fields.Date(
        string='Date d\'expiration',
        help="Date d'expiration du vaccin utilisé"
    )
    
    # Personnel et lieu
    administered_by = fields.Many2one(
        'hr.employee',
        string='Administré par',
        required=True,
        help="Personnel médical qui a administré le vaccin"
    )
    
    location = fields.Char(
        string='Lieu de vaccination',
        help="Lieu où la vaccination a été effectuée"
    )
    
    # Réactions et suivi
    immediate_reaction = fields.Boolean(
        string='Réaction immédiate',
        default=False,
        help="Y a-t-il eu une réaction immédiate?"
    )
    
    reaction_description = fields.Text(
        string='Description de la réaction',
        help="Description de la réaction observée"
    )
    
    reaction_severity = fields.Selection([
        ('mild', 'Légère'),
        ('moderate', 'Modérée'),
        ('severe', 'Sévère')
    ], string='Gravité de la réaction')
    
    # Prochaine dose
    next_dose_due = fields.Date(
        string='Prochaine dose prévue',
        compute='_compute_next_dose_due',
        store=True,
        help="Date prévue pour la prochaine dose"
    )
    
    # Certificat
    certificate_issued = fields.Boolean(
        string='Certificat délivré',
        default=False,
        help="Un certificat de vaccination a-t-il été délivré?"
    )
    
    certificate_number = fields.Char(
        string='Numéro de certificat',
        help="Numéro du certificat de vaccination"
    )
    
    # Notes
    notes = fields.Text(
        string='Notes',
        help="Notes complémentaires sur la vaccination"
    )
    
    # État
    state = fields.Selection([
        ('scheduled', 'Programmée'),
        ('completed', 'Effectuée'),
        ('cancelled', 'Annulée'),
        ('delayed', 'Reportée')
    ], string='État', default='completed', tracking=True)
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    @api.model
    def create(self, vals):
        """Création d'un enregistrement de vaccination"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('vaccination.record') or _('Nouveau')
        return super().create(vals)
    
    @api.depends('vaccination_type_id', 'vaccination_date', 'dose_number')
    def _compute_next_dose_due(self):
        """Calculer la date de la prochaine dose"""
        for record in self:
            if record.vaccination_type_id and record.vaccination_date:
                vaccination_type = record.vaccination_type_id
                if record.dose_number < vaccination_type.doses_required:
                    # Prochaine dose dans la série
                    next_date = fields.Date.from_string(record.vaccination_date) + timedelta(days=vaccination_type.interval_between_doses)
                    record.next_dose_due = next_date
                elif vaccination_type.booster_required:
                    # Rappel
                    next_date = fields.Date.from_string(record.vaccination_date) + timedelta(days=vaccination_type.booster_interval * 365)
                    record.next_dose_due = next_date
                else:
                    record.next_dose_due = False
            else:
                record.next_dose_due = False
    
    @api.constrains('dose_number', 'vaccination_type_id')
    def _check_dose_number(self):
        """Vérifier que le numéro de dose est valide"""
        for record in self:
            if record.dose_number <= 0:
                raise ValidationError(_("Le numéro de dose doit être positif."))
            if record.vaccination_type_id and record.dose_number > record.vaccination_type_id.doses_required:
                raise ValidationError(_("Le numéro de dose ne peut pas dépasser le nombre de doses requises."))
    
    def action_schedule_next_dose(self):
        """Programmer la prochaine dose"""
        if not self.next_dose_due:
            raise UserError(_("Aucune prochaine dose n'est requise pour cette vaccination."))
        
        return {
            'name': _('Programmer la prochaine dose'),
            'type': 'ir.actions.act_window',
            'res_model': 'vaccination.schedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.student_id.id,
                'default_vaccination_type_id': self.vaccination_type_id.id,
                'default_dose_number': self.dose_number + 1,
                'default_scheduled_date': self.next_dose_due
            }
        }


class VaccinationSchedule(models.Model):
    """Planning des vaccinations"""
    _name = 'vaccination.schedule'
    _description = 'Planning de Vaccination'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date'

    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau'),
        help="Référence du planning"
    )
    
    # Relations
    student_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True,
        tracking=True,
        help="Étudiant à vacciner"
    )
    
    vaccination_type_id = fields.Many2one(
        'vaccination.type',
        string='Type de vaccin',
        required=True,
        help="Type de vaccin à administrer"
    )
    
    # Planning
    scheduled_date = fields.Date(
        string='Date programmée',
        required=True,
        tracking=True,
        help="Date prévue pour la vaccination"
    )
    
    scheduled_time = fields.Float(
        string='Heure programmée',
        help="Heure prévue pour la vaccination"
    )
    
    dose_number = fields.Integer(
        string='Numéro de dose',
        required=True,
        default=1,
        help="Numéro de la dose à administrer"
    )
    
    # Rappels
    reminder_sent = fields.Boolean(
        string='Rappel envoyé',
        default=False,
        help="Un rappel a-t-il été envoyé aux parents?"
    )
    
    reminder_date = fields.Date(
        string='Date du rappel',
        help="Date d'envoi du rappel"
    )
    
    # État
    state = fields.Selection([
        ('scheduled', 'Programmée'),
        ('confirmed', 'Confirmée'),
        ('completed', 'Effectuée'),
        ('missed', 'Manquée'),
        ('cancelled', 'Annulée')
    ], string='État', default='scheduled', tracking=True)
    
    # Notes
    notes = fields.Text(
        string='Notes',
        help="Notes sur ce rendez-vous de vaccination"
    )
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    @api.model
    def create(self, vals):
        """Création d'un planning de vaccination"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('vaccination.schedule') or _('Nouveau')
        return super().create(vals)
    
    def action_confirm(self):
        """Confirmer le rendez-vous"""
        self.state = 'confirmed'
    
    def action_complete(self):
        """Marquer comme effectué et créer l'enregistrement"""
        self.state = 'completed'
        
        # Créer l'enregistrement de vaccination
        vaccination_record = self.env['vaccination.record'].create({
            'student_id': self.student_id.id,
            'vaccination_type_id': self.vaccination_type_id.id,
            'vaccination_date': self.scheduled_date,
            'dose_number': self.dose_number,
            'state': 'completed'
        })
        
        return {
            'name': _('Enregistrement de vaccination'),
            'type': 'ir.actions.act_window',
            'res_model': 'vaccination.record',
            'res_id': vaccination_record.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_mark_missed(self):
        """Marquer comme manqué"""
        self.state = 'missed'
    
    def action_cancel(self):
        """Annuler le rendez-vous"""
        self.state = 'cancelled'
    
    @api.model
    def _cron_send_vaccination_reminders(self):
        """Tâche cron pour envoyer les rappels de vaccination"""
        tomorrow = fields.Date.context_today(self) + timedelta(days=1)
        next_week = fields.Date.context_today(self) + timedelta(days=7)
        
        # Rappels pour demain
        schedules_tomorrow = self.search([
            ('scheduled_date', '=', tomorrow),
            ('state', '=', 'scheduled'),
            ('reminder_sent', '=', False)
        ])
        
        # Rappels pour la semaine prochaine
        schedules_next_week = self.search([
            ('scheduled_date', '=', next_week),
            ('state', '=', 'scheduled'),
            ('reminder_sent', '=', False)
        ])
        
        all_schedules = schedules_tomorrow | schedules_next_week
        
        for schedule in all_schedules:
            schedule._send_vaccination_reminder()
            schedule.write({
                'reminder_sent': True,
                'reminder_date': fields.Date.context_today(self)
            })
        
        _logger.info(f"Envoi de {len(all_schedules)} rappels de vaccination")
    
    def _send_vaccination_reminder(self):
        """Envoyer un rappel de vaccination"""
        self.ensure_one()
        # Logique d'envoi de rappel par email/SMS
        template = self.env.ref('edu_health_center.email_template_vaccination_reminder', raise_if_not_found=False)
        if template and self.student_id.email:
            template.send_mail(self.id, force_send=True)
