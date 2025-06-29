# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TransportStudent(models.Model):
    _inherit = 'op.student'

    # Informations de transport
    uses_transport = fields.Boolean('Utilise le transport scolaire')
    transport_subscription_id = fields.Many2one('transport.subscription', 'Abonnement transport')
    
    # Arrêts de transport
    pickup_stop_id = fields.Many2one('transport.route.stop', 'Arrêt de ramassage')
    dropoff_stop_id = fields.Many2one('transport.route.stop', 'Arrêt de dépose')
    
    # Contact d'urgence pour transport
    emergency_contact_name = fields.Char('Contact d\'urgence')
    emergency_contact_phone = fields.Char('Téléphone urgence')
    
    # Informations médicales pour transport
    medical_conditions = fields.Text('Conditions médicales')
    medications = fields.Text('Médicaments')
    allergies = fields.Text('Allergies')
    
    # Autorisations
    transport_authorization = fields.Boolean('Autorisation parentale', default=False)
    photo_authorization = fields.Boolean('Autorisation photo/vidéo', default=False)
    
    # Historique des trajets
    trip_history_ids = fields.Many2many('transport.trip', string='Historique trajets')
    
    # Statistiques
    total_trips = fields.Integer('Total trajets', compute='_compute_transport_stats')
    missed_trips = fields.Integer('Trajets manqués', compute='_compute_transport_stats')
    
    @api.depends('trip_history_ids')
    def _compute_transport_stats(self):
        for student in self:
            student.total_trips = len(student.trip_history_ids)
            # Calculer les trajets manqués (logique à implémenter selon les besoins)
            student.missed_trips = 0


class TransportSubscription(models.Model):
    _name = 'transport.subscription'
    _description = 'Abonnement Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Référence', required=True, default=lambda self: _('Nouveau'))
    student_id = fields.Many2one('op.student', 'Étudiant', required=True, tracking=True)
    
    # Période
    start_date = fields.Date('Date de début', required=True, tracking=True)
    end_date = fields.Date('Date de fin', required=True, tracking=True)
    
    # Type d'abonnement
    subscription_type = fields.Selection([
        ('monthly', 'Mensuel'),
        ('quarterly', 'Trimestriel'),
        ('semester', 'Semestriel'),
        ('annual', 'Annuel')
    ], string='Type d\'abonnement', required=True, default='monthly')
    
    # Itinéraires
    route_ids = fields.Many2many('transport.route', string='Itinéraires')
    
    # Tarification
    base_price = fields.Float('Prix de base', required=True)
    discount_percent = fields.Float('Remise (%)')
    final_price = fields.Float('Prix final', compute='_compute_final_price', store=True)
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('suspended', 'Suspendu'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé')
    ], default='draft', string='Statut', tracking=True)
    
    # Paiement
    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement'),
        ('check', 'Chèque'),
        ('card', 'Carte bancaire'),
        ('online', 'Paiement en ligne')
    ], string='Mode de paiement')
    
    payment_status = fields.Selection([
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('partial', 'Partiellement payé'),
        ('overdue', 'En retard')
    ], string='Statut paiement', default='pending')
    
    # Factures
    invoice_ids = fields.One2many('account.move', 'transport_subscription_id', 'Factures')
    
    @api.depends('base_price', 'discount_percent')
    def _compute_final_price(self):
        for subscription in self:
            discount_amount = subscription.base_price * (subscription.discount_percent / 100)
            subscription.final_price = subscription.base_price - discount_amount
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.subscription') or _('Nouveau')
        return super(TransportSubscription, self).create(vals)
    
    def action_activate(self):
        self.state = 'active'
    
    def action_suspend(self):
        self.state = 'suspended'
    
    def action_cancel(self):
        self.state = 'cancelled'
    
    def generate_invoice(self):
        """Générer une facture pour l'abonnement"""
        invoice_vals = {
            'partner_id': self.student_id.partner_id.id,
            'move_type': 'out_invoice',
            'transport_subscription_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': f'Abonnement transport - {self.name}',
                'quantity': 1,
                'price_unit': self.final_price,
            })]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        return invoice


class TransportStudentAttendance(models.Model):
    _name = 'transport.student.attendance'
    _description = 'Présence Étudiant Transport'

    student_id = fields.Many2one('op.student', 'Étudiant', required=True)
    trip_id = fields.Many2one('transport.trip', 'Trajet', required=True)
    stop_id = fields.Many2one('transport.route.stop', 'Arrêt')
    
    # Présence
    boarded = fields.Boolean('Monté dans le bus')
    alighted = fields.Boolean('Descendu du bus')
    
    # Horodatage
    board_time = fields.Datetime('Heure de montée')
    alight_time = fields.Datetime('Heure de descente')
    
    # Statut
    status = fields.Selection([
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('late', 'En retard'),
        ('early', 'En avance')
    ], string='Statut', compute='_compute_status')
    
    # Notes
    notes = fields.Text('Observations')
    
    @api.depends('boarded', 'alighted', 'board_time')
    def _compute_status(self):
        for attendance in self:
            if attendance.boarded:
                attendance.status = 'present'
            else:
                attendance.status = 'absent'


# Extension du modèle account.move pour les factures de transport
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    transport_subscription_id = fields.Many2one('transport.subscription', 'Abonnement transport')
