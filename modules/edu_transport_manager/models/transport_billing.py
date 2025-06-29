# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class TransportBilling(models.Model):
    _name = 'transport.billing'
    _description = 'Facturation Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char('Référence', required=True, default=lambda self: _('Nouveau'))
    student_id = fields.Many2one('op.student', 'Étudiant', required=True, tracking=True)
    subscription_id = fields.Many2one('transport.subscription', 'Abonnement', tracking=True)
    
    # Période de facturation
    date = fields.Date('Date de facturation', required=True, default=fields.Date.today, tracking=True)
    period_start = fields.Date('Début période', required=True)
    period_end = fields.Date('Fin période', required=True)
    
    # Montants
    base_amount = fields.Float('Montant de base', required=True)
    discount_amount = fields.Float('Remise')
    penalty_amount = fields.Float('Pénalités')
    total_amount = fields.Float('Montant total', compute='_compute_total_amount', store=True)
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('invoiced', 'Facturée'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée')
    ], default='draft', string='Statut', tracking=True)
    
    # Facturation
    invoice_id = fields.Many2one('account.move', 'Facture', tracking=True)
    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement'),
        ('check', 'Chèque'),
        ('card', 'Carte bancaire'),
        ('online', 'Paiement en ligne')
    ], string='Mode de paiement')
    
    # Détails
    description = fields.Text('Description')
    notes = fields.Text('Notes')
    
    @api.depends('base_amount', 'discount_amount', 'penalty_amount')
    def _compute_total_amount(self):
        for billing in self:
            billing.total_amount = billing.base_amount - billing.discount_amount + billing.penalty_amount
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.billing') or _('Nouveau')
        return super(TransportBilling, self).create(vals)
    
    def action_confirm(self):
        self.state = 'confirmed'
    
    def action_create_invoice(self):
        """Créer une facture pour cette facturation"""
        if self.invoice_id:
            raise ValidationError(_('Une facture existe déjà pour cette facturation.'))
        
        invoice_vals = {
            'partner_id': self.student_id.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.date,
            'transport_billing_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': f'Transport scolaire - Période du {self.period_start} au {self.period_end}',
                'quantity': 1,
                'price_unit': self.total_amount,
            })]
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id
        self.state = 'invoiced'
        return invoice
    
    def action_cancel(self):
        self.state = 'cancelled'


class TransportTariff(models.Model):
    _name = 'transport.tariff'
    _description = 'Tarif Transport'

    name = fields.Char('Nom du tarif', required=True)
    route_id = fields.Many2one('transport.route', 'Itinéraire')
    
    # Type de tarif
    tariff_type = fields.Selection([
        ('fixed', 'Forfait fixe'),
        ('distance', 'Basé sur la distance'),
        ('zone', 'Basé sur les zones')
    ], string='Type de tarif', required=True, default='fixed')
    
    # Montants
    base_price = fields.Float('Prix de base', required=True)
    price_per_km = fields.Float('Prix par km')
    
    # Période de validité
    valid_from = fields.Date('Valide à partir de', required=True)
    valid_to = fields.Date('Valide jusqu\'au')
    
    # Remises
    discount_ids = fields.One2many('transport.tariff.discount', 'tariff_id', 'Remises')
    
    # Statut
    active = fields.Boolean('Actif', default=True)
    
    def get_price(self, distance=0, student_count=1):
        """Calculer le prix selon le type de tarif"""
        if self.tariff_type == 'fixed':
            return self.base_price
        elif self.tariff_type == 'distance':
            return self.base_price + (distance * self.price_per_km)
        else:
            return self.base_price


class TransportTariffDiscount(models.Model):
    _name = 'transport.tariff.discount'
    _description = 'Remise Tarif Transport'

    tariff_id = fields.Many2one('transport.tariff', 'Tarif', required=True, ondelete='cascade')
    name = fields.Char('Nom de la remise', required=True)
    
    # Type de remise
    discount_type = fields.Selection([
        ('percentage', 'Pourcentage'),
        ('fixed', 'Montant fixe')
    ], string='Type de remise', required=True, default='percentage')
    
    # Valeur de la remise
    discount_value = fields.Float('Valeur de la remise', required=True)
    
    # Conditions
    min_students = fields.Integer('Nombre minimum d\'étudiants')
    student_category = fields.Selection([
        ('all', 'Tous'),
        ('scholarship', 'Boursiers'),
        ('siblings', 'Fratrie')
    ], string='Catégorie d\'étudiants', default='all')
    
    # Période
    valid_from = fields.Date('Valide à partir de')
    valid_to = fields.Date('Valide jusqu\'au')
    
    def calculate_discount(self, base_amount):
        """Calculer le montant de la remise"""
        if self.discount_type == 'percentage':
            return base_amount * (self.discount_value / 100)
        else:
            return self.discount_value


class TransportPayment(models.Model):
    _name = 'transport.payment'
    _description = 'Paiement Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Référence', required=True, default=lambda self: _('Nouveau'))
    billing_id = fields.Many2one('transport.billing', 'Facturation', required=True, tracking=True)
    student_id = fields.Many2one('op.student', 'Étudiant', related='billing_id.student_id', store=True)
    
    # Paiement
    date = fields.Date('Date de paiement', required=True, default=fields.Date.today, tracking=True)
    amount = fields.Float('Montant', required=True, tracking=True)
    
    # Mode de paiement
    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement'),
        ('check', 'Chèque'),
        ('card', 'Carte bancaire'),
        ('online', 'Paiement en ligne')
    ], string='Mode de paiement', required=True, tracking=True)
    
    # Détails du paiement
    reference = fields.Char('Référence de paiement')
    bank_account = fields.Char('Compte bancaire')
    check_number = fields.Char('Numéro de chèque')
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('reconciled', 'Rapproché'),
        ('cancelled', 'Annulé')
    ], default='draft', string='Statut', tracking=True)
    
    # Notes
    notes = fields.Text('Notes')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.payment') or _('Nouveau')
        return super(TransportPayment, self).create(vals)
    
    def action_confirm(self):
        self.state = 'confirmed'
        # Mettre à jour le statut de la facturation si entièrement payée
        if self.billing_id.total_amount <= sum(self.billing_id.payment_ids.filtered(lambda p: p.state == 'confirmed').mapped('amount')):
            self.billing_id.state = 'paid'
    
    def action_cancel(self):
        self.state = 'cancelled'


# Extension du modèle account.move pour les factures de transport
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    transport_billing_id = fields.Many2one('transport.billing', 'Facturation transport')


class TransportBillingLine(models.Model):
    _name = 'transport.billing.line'
    _description = 'Ligne de Facturation Transport'

    billing_id = fields.Many2one('transport.billing', 'Facturation', required=True, ondelete='cascade')
    trip_id = fields.Many2one('transport.trip', 'Trajet')
    
    # Description
    description = fields.Char('Description', required=True)
    
    # Quantité et prix
    quantity = fields.Float('Quantité', default=1.0)
    unit_price = fields.Float('Prix unitaire')
    total_price = fields.Float('Prix total', compute='_compute_total_price', store=True)
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        for line in self:
            line.total_price = line.quantity * line.unit_price
