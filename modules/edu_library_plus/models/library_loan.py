# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = 'Prêt de Livre'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'loan_date desc'

    name = fields.Char(
        string='Référence',
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
        required=True,
        tracking=True
    )
    
    loan_date = fields.Datetime(
        string='Date d\'Emprunt',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    
    due_date = fields.Datetime(
        string='Date d\'Échéance',
        compute='_compute_due_date',
        store=True,
        tracking=True
    )
    
    return_date = fields.Datetime(
        string='Date de Retour',
        tracking=True
    )
    
    state = fields.Selection([
        ('active', 'Actif'),
        ('returned', 'Retourné'),
        ('overdue', 'En Retard'),
        ('lost', 'Perdu'),
        ('cancelled', 'Annulé')
    ], string='État', default='active', required=True, tracking=True)
    
    notes = fields.Text(
        string='Notes'
    )
    
    fine_amount = fields.Float(
        string='Montant de l\'Amende',
        default=0.0
    )
    
    is_overdue = fields.Boolean(
        string='En Retard',
        compute='_compute_is_overdue',
        store=True
    )
    
    days_overdue = fields.Integer(
        string='Jours de Retard',
        compute='_compute_days_overdue',
        store=True
    )
    
    @api.depends('loan_date')
    def _compute_due_date(self):
        for loan in self:
            if loan.loan_date:
                # 14 jours par défaut
                loan.due_date = loan.loan_date + timedelta(days=14)
    
    @api.depends('due_date', 'return_date', 'state')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for loan in self:
            loan.is_overdue = (
                loan.state == 'active' and 
                loan.due_date and 
                loan.due_date < now
            )
    
    @api.depends('due_date', 'return_date', 'state')
    def _compute_days_overdue(self):
        now = fields.Datetime.now()
        for loan in self:
            if loan.is_overdue:
                delta = now - loan.due_date
                loan.days_overdue = delta.days
            else:
                loan.days_overdue = 0
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('library.loan') or _('Nouveau')
        return super().create(vals)
    
    def action_return(self):
        """Retourner le livre"""
        self.ensure_one()
        self.write({
            'state': 'returned',
            'return_date': fields.Datetime.now()
        })
        
        # Mettre à jour l'état du livre
        self.book_id._compute_copies_loaned()
        self.book_id._compute_copies_available()
        self.book_id._compute_is_available()
    
    def action_renew(self):
        """Renouveler l'emprunt"""
        self.ensure_one()
        if self.state == 'active':
            new_due_date = self.due_date + timedelta(days=14)
            self.due_date = new_due_date
            self.message_post(body=_('Emprunt renouvelé jusqu\'au %s') % new_due_date.strftime('%d/%m/%Y'))
    
    def action_mark_lost(self):
        """Marquer comme perdu"""
        self.ensure_one()
        self.state = 'lost'
        self.message_post(body=_('Livre marqué comme perdu'))
    
    def action_cancel(self):
        """Annuler l'emprunt"""
        self.ensure_one()
        self.state = 'cancelled'
