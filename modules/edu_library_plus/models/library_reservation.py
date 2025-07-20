# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class LibraryReservation(models.Model):
    _name = 'library.reservation'
    _description = 'Réservation de Livre'
    _order = 'reservation_date desc'

    name = fields.Char(
        string='Numéro de Réservation',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )
    
    member_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True,
        tracking=True
    )
    
    book_id = fields.Many2one(
        'library.book',
        string='Livre',
        required=True
    )
    
    reservation_date = fields.Datetime(
        string='Date de Réservation',
        default=fields.Datetime.now,
        required=True
    )
    
    expiry_date = fields.Datetime(
        string='Date d\'Expiration',
        compute='_compute_expiry_date',
        store=True
    )
    
    state = fields.Selection([
        ('pending', 'En Attente'),
        ('available', 'Disponible'),
        ('collected', 'Récupéré'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé')
    ], string='État', default='pending', required=True)
    
    priority = fields.Selection([
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevé'),
        ('urgent', 'Urgent')
    ], string='Priorité', default='normal')
    
    notes = fields.Text(
        string='Notes'
    )
    
    notification_sent = fields.Boolean(
        string='Notification Envoyée',
        default=False
    )
    
    collected_date = fields.Datetime(
        string='Date de Récupération'
    )
    
    loan_id = fields.Many2one(
        'library.loan',
        string='Prêt Associé'
    )
    
    @api.depends('reservation_date')
    def _compute_expiry_date(self):
        for reservation in self:
            if reservation.reservation_date:
                reservation.expiry_date = reservation.reservation_date + timedelta(days=7)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('library.reservation') or _('Nouveau')
        return super().create(vals)
    
    def action_make_available(self):
        """Marquer la réservation comme disponible"""
        self.state = 'available'
        self._send_notification()
    
    def action_collect(self):
        """Marquer la réservation comme récupérée"""
        self.state = 'collected'
        self.collected_date = fields.Datetime.now()
        # Créer automatiquement un prêt
        loan_vals = {
            'member_id': self.member_id.id,
            'book_id': self.book_id.id,
            'reservation_id': self.id,
        }
        loan = self.env['library.loan'].create(loan_vals)
        self.loan_id = loan.id
    
    def action_cancel(self):
        """Annuler la réservation"""
        self.state = 'cancelled'
    
    def action_expire(self):
        """Marquer la réservation comme expirée"""
        self.state = 'expired'
    
    def _send_notification(self):
        """Envoyer une notification au membre"""
        if not self.notification_sent and self.member_id.email:
            template = self.env.ref('edu_library_plus.email_template_reservation_available', False)
            if template:
                template.send_mail(self.id, force_send=True)
                self.notification_sent = True
    
    @api.model
    def _cron_check_expired_reservations(self):
        """Cron job pour vérifier les réservations expirées"""
        expired_reservations = self.search([
            ('state', '=', 'available'),
            ('expiry_date', '<', fields.Datetime.now())
        ])
        expired_reservations.action_expire()
