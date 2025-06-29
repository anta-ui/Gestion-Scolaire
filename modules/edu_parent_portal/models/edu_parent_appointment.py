# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class EduParentAppointment(models.Model):
    """Rendez-vous entre parents et enseignants"""
    _name = 'edu.parent.appointment'
    _description = 'Rendez-vous parent'
    _order = 'appointment_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Référence',
        required=True,
        default=lambda self: _('Nouveau'),
        help="Référence du rendez-vous"
    )
    
    parent_id = fields.Many2one(
        'res.partner',
        string='Parent',
        required=True,
        domain=[('is_parent', '=', True)],
        help="Parent demandeur"
    )
    
    teacher_id = fields.Many2one(
        'op.faculty',
        string='Enseignant',
        required=True,
        help="Enseignant concerné"
    )
    
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        help="Élève concerné"
    )
    
    appointment_date = fields.Datetime(
        string='Date du rendez-vous',
        required=True,
        help="Date et heure du rendez-vous"
    )
    
    duration = fields.Float(
        string='Durée (heures)',
        default=0.5,
        help="Durée en heures"
    )
    
    subject = fields.Char(
        string='Sujet',
        required=True,
        help="Sujet du rendez-vous"
    )
    
    description = fields.Text(
        string='Description',
        help="Description détaillée"
    )
    
    location = fields.Char(
        string='Lieu',
        help="Lieu du rendez-vous"
    )
    
    meeting_type = fields.Selection([
        ('physical', 'Présentiel'),
        ('online', 'En ligne'),
        ('phone', 'Téléphone')
    ], string='Type de rencontre', default='physical', required=True)
    
    meeting_url = fields.Char(
        string='URL de réunion',
        help="Lien pour réunion en ligne"
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('requested', 'Demandé'),
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé'),
        ('completed', 'Terminé')
    ], string='État', default='draft', help="État du rendez-vous", tracking=True)
    
    priority = fields.Selection([
        ('0', 'Normale'),
        ('1', 'Importante'),
        ('2', 'Urgente')
    ], string='Priorité', default='0')
    
    # Notes du rendez-vous
    parent_notes = fields.Text(
        string='Notes du parent',
        help="Notes du parent"
    )
    
    teacher_notes = fields.Text(
        string='Notes de l\'enseignant',
        help="Notes de l'enseignant"
    )
    
    # Rappels
    reminder_sent = fields.Boolean(
        string='Rappel envoyé',
        default=False,
        help="Rappel envoyé"
    )
    
    reminder_date = fields.Datetime(
        string='Date de rappel',
        compute='_compute_reminder_date',
        store=True,
        help="Date d'envoi du rappel"
    )
    
    @api.depends('appointment_date')
    def _compute_reminder_date(self):
        for record in self:
            if record.appointment_date:
                record.reminder_date = record.appointment_date - timedelta(hours=24)
            else:
                record.reminder_date = False
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('edu.parent.appointment') or _('Nouveau')
        return super().create(vals)
    
    def action_request(self):
        """Demander le rendez-vous"""
        self.write({'state': 'requested'})
        self._send_request_notification()
    
    def action_confirm(self):
        """Confirmer le rendez-vous"""
        self.write({'state': 'confirmed'})
        self._send_confirmation_notification()
    
    def action_cancel(self):
        """Annuler le rendez-vous"""
        self.write({'state': 'cancelled'})
        self._send_cancellation_notification()
    
    def action_complete(self):
        """Marquer comme terminé"""
        self.write({'state': 'completed'})
    
    def _send_request_notification(self):
        """Envoyer notification de demande"""
        # Logique de notification
        pass
    
    def _send_confirmation_notification(self):
        """Envoyer notification de confirmation"""
        # Logique de notification
        pass
    
    def _send_cancellation_notification(self):
        """Envoyer notification d'annulation"""
        # Logique de notification
        pass
