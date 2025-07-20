# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EduStudentPayment(models.Model):
    _name = 'edu.student.payment'
    _description = 'Paiement Étudiant'
    _rec_name = 'name'
    _order = 'payment_date desc, id desc'

    name = fields.Char(
        string='Référence Paiement',
        required=True,
        default=lambda self: _('Nouveau Paiement'),
        copy=False
    )
    
    student_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True,
        ondelete='cascade'
    )
    
    invoice_id = fields.Many2one(
        'edu.student.invoice',
        string='Facture',
        ondelete='cascade'
    )
    
    amount = fields.Float(
        string='Montant',
        required=True
    )
    
    payment_date = fields.Date(
        string='Date de Paiement',
        required=True,
        default=fields.Date.context_today
    )
    
    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('check', 'Chèque'),
        ('bank_transfer', 'Virement Bancaire'),
        ('credit_card', 'Carte de Crédit'),
        ('mobile_money', 'Mobile Money'),
        ('online', 'Paiement en Ligne')
    ], string='Mode de Paiement', required=True, default='cash')
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('reconciled', 'Lettré'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    notes = fields.Text(string='Notes')
    
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nouveau Paiement')) == _('Nouveau Paiement'):
                vals['name'] = self.env['ir.sequence'].next_by_code('edu.student.payment') or _('Nouveau Paiement')
        return super().create(vals_list)

    def confirm_payment(self):
        """Confirme le paiement"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Seuls les paiements en brouillon peuvent être confirmés."))
            record.state = 'confirmed'
        return True

    def cancel_payment(self):
        """Annule le paiement"""
        for record in self:
            if record.state == 'reconciled':
                raise UserError(_("Impossible d'annuler un paiement lettré."))
            record.state = 'cancelled'
        return True
