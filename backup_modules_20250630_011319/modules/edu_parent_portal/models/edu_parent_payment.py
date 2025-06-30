# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EduParentPayment(models.Model):
    """Paiements et facturation pour les parents"""
    _name = 'edu.parent.payment'
    _description = 'Paiement parent'
    _order = 'due_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Référence',
        required=True,
        default=lambda self: _('Nouveau'),
        help="Référence du paiement"
    )
    
    description = fields.Text(
        string='Description',
        help="Description du paiement"
    )
    
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        help="Élève concerné"
    )
    
    parent_id = fields.Many2one(
        'res.partner',
        string='Parent',
        required=True,
        domain=[('is_parent', '=', True)],
        help="Parent responsable du paiement"
    )
    
    payment_type = fields.Selection([
        ('tuition', 'Frais de scolarité'),
        ('registration', 'Frais d\'inscription'),
        ('activity', 'Activités'),
        ('transport', 'Transport'),
        ('meal', 'Restauration'),
        ('book', 'Manuels scolaires'),
        ('uniform', 'Uniforme'),
        ('trip', 'Sortie scolaire'),
        ('medical', 'Frais médicaux'),
        ('penalty', 'Pénalité'),
        ('other', 'Autre')
    ], string='Type de paiement', required=True, help="Type de paiement")
    
    amount = fields.Monetary(
        string='Montant',
        required=True,
        help="Montant à payer"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
        help="Devise du paiement"
    )
    
    due_date = fields.Date(
        string='Date d\'échéance',
        required=True,
        help="Date limite de paiement"
    )
    
    invoice_date = fields.Date(
        string='Date de facture',
        default=fields.Date.today,
        help="Date de la facture"
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('partial', 'Partiellement payé'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', help="État du paiement", tracking=True)
    
    # Montants calculés
    paid_amount = fields.Monetary(
        string='Montant payé',
        compute='_compute_amounts',
        store=True,
        help="Montant déjà payé"
    )
    
    remaining_amount = fields.Monetary(
        string='Montant restant',
        compute='_compute_amounts',
        store=True,
        help="Montant restant à payer"
    )
    
    # Paiements associés
    payment_ids = fields.One2many(
        'edu.payment.transaction',
        'parent_payment_id',
        string='Transactions',
        help="Transactions de paiement"
    )
    
    # Facture associée
    invoice_id = fields.Many2one(
        'account.move',
        string='Facture',
        help="Facture comptable associée"
    )
    
    # Rappels et notifications
    reminder_count = fields.Integer(
        string='Nombre de rappels',
        default=0,
        help="Nombre de rappels envoyés"
    )
    
    last_reminder_date = fields.Date(
        string='Dernier rappel',
        help="Date du dernier rappel"
    )
    
    # Paiement en ligne
    allow_online_payment = fields.Boolean(
        string='Paiement en ligne autorisé',
        default=True,
        help="Autoriser le paiement en ligne"
    )
    
    payment_methods = fields.Many2many(
        'payment.provider',
        string='Méthodes de paiement',
        help="Méthodes de paiement acceptées"
    )
    
    @api.depends('payment_ids.amount', 'amount')
    def _compute_amounts(self):
        for record in self:
            paid_amount = sum(record.payment_ids.filtered(lambda p: p.state == 'done').mapped('amount'))
            record.paid_amount = paid_amount
            record.remaining_amount = record.amount - paid_amount
            
            # Mettre à jour l'état selon les montants
            if record.remaining_amount <= 0:
                record.state = 'paid'
            elif record.paid_amount > 0:
                record.state = 'partial'
            elif record.due_date < fields.Date.today() and record.state not in ['paid', 'cancelled']:
                record.state = 'overdue'
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('edu.parent.payment') or _('Nouveau')
        return super().create(vals)
    
    def action_send_reminder(self):
        """Envoyer un rappel de paiement"""
        for record in self:
            record.write({
                'reminder_count': record.reminder_count + 1,
                'last_reminder_date': fields.Date.today()
            })
            record._send_payment_reminder()
    
    def action_pay_online(self):
        """Rediriger vers le paiement en ligne"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/payment/parent/{self.id}',
            'target': 'new',
        }
    
    def action_mark_paid(self):
        """Marquer comme payé manuellement"""
        self.write({'state': 'paid'})
        self._create_payment_transaction(self.remaining_amount, 'manual')
    
    def action_cancel(self):
        """Annuler le paiement"""
        self.write({'state': 'cancelled'})
    
    def _send_payment_reminder(self):
        """Envoyer rappel de paiement"""
        notification_obj = self.env['edu.parent.notification']
        if self.parent_id.user_ids:
            notification_obj.create({
                'title': f'Rappel de paiement: {self.name}',
                'message': f'Le paiement de {self.amount} {self.currency_id.symbol} pour {self.student_id.name} est dû le {self.due_date}.',
                'category': 'payment',
                'notification_type': 'warning',
                'recipient_ids': [(6, 0, self.parent_id.user_ids.ids)],
                'student_ids': [(6, 0, [self.student_id.id])],
                'state': 'sent',
                'send_date': fields.Datetime.now()
            })
    
    def _create_payment_transaction(self, amount, method):
        """Créer une transaction de paiement"""
        return self.env['edu.payment.transaction'].create({
            'parent_payment_id': self.id,
            'amount': amount,
            'payment_method': method,
            'state': 'done',
            'transaction_date': fields.Datetime.now()
        })


class EduPaymentTransaction(models.Model):
    """Transaction de paiement"""
    _name = 'edu.payment.transaction'
    _description = 'Transaction de paiement'
    _order = 'transaction_date desc'
    _rec_name = 'reference'

    reference = fields.Char(
        string='Référence',
        required=True,
        default=lambda self: _('Nouveau'),
        help="Référence de la transaction"
    )
    
    parent_payment_id = fields.Many2one(
        'edu.parent.payment',
        string='Paiement parent',
        required=True,
        help="Paiement parent associé"
    )
    
    amount = fields.Monetary(
        string='Montant',
        required=True,
        help="Montant de la transaction"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='parent_payment_id.currency_id',
        help="Devise de la transaction"
    )
    
    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('check', 'Chèque'),
        ('transfer', 'Virement'),
        ('card', 'Carte bancaire'),
        ('mobile', 'Paiement mobile'),
        ('online', 'Paiement en ligne'),
        ('manual', 'Manuel')
    ], string='Méthode de paiement', required=True, help="Méthode de paiement")
    
    state = fields.Selection([
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('done', 'Terminé'),
        ('failed', 'Échec'),
        ('cancelled', 'Annulé')
    ], string='État', default='pending', help="État de la transaction")
    
    transaction_date = fields.Datetime(
        string='Date de transaction',
        default=fields.Datetime.now,
        help="Date de la transaction"
    )
    
    provider_reference = fields.Char(
        string='Référence fournisseur',
        help="Référence du fournisseur de paiement"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Notes sur la transaction"
    )
    
    @api.model
    def create(self, vals):
        if vals.get('reference', _('Nouveau')) == _('Nouveau'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('edu.payment.transaction') or _('Nouveau')
        return super().create(vals)
