# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class VaccinationType(models.Model):
    """Types de vaccins"""
    _name = 'vaccination.type'
    _description = 'Type de Vaccin'
    _order = 'name'

    # Informations de base
    name = fields.Char(
        string='Nom du vaccin',
        required=True
    )

    description = fields.Text(
        string='Description'
    )

    # Propriétés du vaccin
    disease_prevented = fields.Char(
        string='Maladie prévenue',
        required=True
    )

    age_category = fields.Selection([
        ('infant', 'Nourrisson (0-2 ans)'),
        ('child', 'Enfant (2-12 ans)'),
        ('adolescent', 'Adolescent (12-18 ans)'),
        ('adult', 'Adulte (18+ ans)'),
        ('all', 'Tous âges'),
    ], string='Catégorie d\'âge', default='all')

    # Calendrier vaccinal
    required = fields.Boolean(
        string='Obligatoire',
        default=False,
        help='Vaccin obligatoire selon le calendrier vaccinal'
    )

    doses_required = fields.Integer(
        string='Nombre de doses',
        default=1
    )

    interval_between_doses = fields.Integer(
        string='Intervalle entre doses (jours)',
        default=0
    )

    booster_required = fields.Boolean(
        string='Rappel nécessaire',
        default=False
    )

    booster_interval_years = fields.Integer(
        string='Intervalle rappel (années)',
        default=5
    )

    # Informations médicales
    contraindications = fields.Text(
        string='Contre-indications'
    )

    side_effects = fields.Text(
        string='Effets secondaires possibles'
    )

    # État
    active = fields.Boolean(
        string='Actif',
        default=True
    )


class VaccinationRecord(models.Model):
    """Dossier de vaccination individuel"""
    _name = 'vaccination.record'
    _description = 'Dossier de Vaccination'
    _order = 'vaccination_date desc'

    # Informations de base
    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )

    # Patient
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        required=True
    )

    student_id = fields.Many2one(
        related='health_record_id.student_id',
        string='Étudiant',
        readonly=True,
        store=True
    )

    # Vaccination
    vaccination_type_id = fields.Many2one(
        'vaccination.type',
        string='Type de vaccin',
        required=True
    )

    vaccination_date = fields.Date(
        string='Date de vaccination',
        required=True,
        default=fields.Date.today
    )

    dose_number = fields.Integer(
        string='Numéro de dose',
        default=1
    )

    # Informations du vaccin
    vaccine_batch = fields.Char(
        string='Numéro de lot'
    )

    vaccine_manufacturer = fields.Char(
        string='Fabricant'
    )

    expiry_date = fields.Date(
        string='Date d\'expiration'
    )

    # Personnel médical
    administered_by = fields.Many2one(
        'res.users',
        string='Administré par',
        required=True,
        default=lambda self: self.env.user
    )

    # Localisation
    injection_site = fields.Selection([
        ('left_arm', 'Bras gauche'),
        ('right_arm', 'Bras droit'),
        ('left_thigh', 'Cuisse gauche'),
        ('right_thigh', 'Cuisse droite'),
        ('other', 'Autre'),
    ], string='Site d\'injection', default='left_arm')

    # Réactions
    adverse_reaction = fields.Boolean(
        string='Réaction indésirable',
        default=False
    )

    reaction_description = fields.Text(
        string='Description de la réaction'
    )

    reaction_severity = fields.Selection([
        ('mild', 'Légère'),
        ('moderate', 'Modérée'),
        ('severe', 'Sévère'),
    ], string='Gravité de la réaction')

    # État
    state = fields.Selection([
        ('scheduled', 'Programmé'),
        ('administered', 'Administré'),
        ('missed', 'Raté'),
        ('cancelled', 'Annulé'),
    ], string='État', default='scheduled')

    # Dates importantes
    next_dose_date = fields.Date(
        string='Prochaine dose prévue',
        compute='_compute_next_dose_date',
        store=True
    )

    next_booster_date = fields.Date(
        string='Prochain rappel prévu',
        compute='_compute_next_booster_date',
        store=True
    )

    @api.depends('vaccination_type_id', 'vaccination_date', 'dose_number')
    def _compute_next_dose_date(self):
        """Calculer la date de la prochaine dose"""
        for record in self:
            if (record.vaccination_type_id and 
                record.vaccination_date and 
                record.dose_number < record.vaccination_type_id.doses_required):
                
                interval = record.vaccination_type_id.interval_between_doses
                if interval > 0:
                    record.next_dose_date = record.vaccination_date + timedelta(days=interval)
                else:
                    record.next_dose_date = False
            else:
                record.next_dose_date = False

    @api.depends('vaccination_type_id', 'vaccination_date', 'dose_number')
    def _compute_next_booster_date(self):
        """Calculer la date du prochain rappel"""
        for record in self:
            if (record.vaccination_type_id and 
                record.vaccination_date and 
                record.vaccination_type_id.booster_required and
                record.dose_number >= record.vaccination_type_id.doses_required):
                
                interval_years = record.vaccination_type_id.booster_interval_years
                record.next_booster_date = record.vaccination_date + timedelta(days=interval_years * 365)
            else:
                record.next_booster_date = False

    # Actions
    def action_administer(self):
        """Administrer le vaccin"""
        self.write({
            'state': 'administered',
            'vaccination_date': fields.Date.today()
        })
        return True

    def action_cancel(self):
        """Annuler la vaccination"""
        self.state = 'cancelled'
        return True

    @api.model
    def create(self, vals):
        """Génération automatique du numéro de vaccination"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('vaccination.record') or _('Nouveau')
        return super().create(vals)


class VaccinationSchedule(models.Model):
    """Planning des vaccinations"""
    _name = 'vaccination.schedule'
    _description = 'Planning de Vaccination'
    _order = 'scheduled_date'

    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau')
    )
    
    # Patient
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        required=True
    )

    student_id = fields.Many2one(
        related='health_record_id.student_id',
        string='Étudiant',
        readonly=True,
        store=True
    )
    
    vaccination_type_id = fields.Many2one(
        'vaccination.type',
        string='Type de vaccin',
        required=True
    )
    
    # Planning
    scheduled_date = fields.Date(
        string='Date programmée',
        required=True
    )
    
    scheduled_time = fields.Float(
        string='Heure programmée'
    )
    
    dose_number = fields.Integer(
        string='Numéro de dose',
        required=True,
        default=1
    )
    
    # Rappels
    reminder_sent = fields.Boolean(
        string='Rappel envoyé',
        default=False
    )
    
    reminder_date = fields.Date(
        string='Date du rappel'
    )
    
    # État
    state = fields.Selection([
        ('scheduled', 'Programmée'),
        ('confirmed', 'Confirmée'),
        ('completed', 'Effectuée'),
        ('missed', 'Manquée'),
        ('cancelled', 'Annulée')
    ], string='État', default='scheduled')
    
    # Notes
    notes = fields.Text(
        string='Notes'
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
