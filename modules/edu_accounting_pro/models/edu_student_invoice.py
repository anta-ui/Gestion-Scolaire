# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class EduStudentInvoice(models.Model):
    """Factures spécifiques aux étudiants"""
    _name = 'edu.student.invoice'
    _description = 'Facture Étudiant'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'invoice_date desc, number desc'
    _rec_name = 'number'

    # Référence et identification
    number = fields.Char(
        string='Numéro de facture',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau'),
        help="Numéro unique de la facture"
    )
    
    reference = fields.Char(
        string='Référence externe',
        help="Référence externe ou numéro de commande"
    )
    
    # Relations principales avec OpenEduCat
    student_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True,
        tracking=True,
        help="Étudiant concerné par la facture"
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Responsable financier',
        compute='_compute_partner_id',
        store=True,
        help="Contact responsable du paiement"
    )
    
    academic_year_id = fields.Many2one(
        'op.academic.year',
        string='Année scolaire',
        required=True,
        default=lambda self: self.env['op.academic.year'].search([], limit=1),
        help="Année scolaire de la facture"
    )
    
    course_id = fields.Many2one(
        'op.course',
        string='Cours',
        help="Cours de l'étudiant"
    )
    
    batch_id = fields.Many2one(
        'op.batch',
        string='Batch',
        help="Batch de l'étudiant"
    )
    
    # Dates
    invoice_date = fields.Date(
        string='Date de facture',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date d'émission de la facture"
    )
    
    due_date = fields.Date(
        string='Date d\'échéance',
        required=True,
        tracking=True,
        help="Date limite de paiement"
    )
    
    period_start = fields.Date(
        string='Début de période',
        help="Date de début de la période facturée"
    )
    
    period_end = fields.Date(
        string='Fin de période',
        help="Date de fin de la période facturée"
    )
    
    # Montants
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Devise de la facture"
    )
    
    amount_untaxed = fields.Monetary(
        string='Montant HT',
        currency_field='currency_id',
        store=True,
        compute='_compute_amounts',
        help="Montant hors taxes"
    )
    
    amount_tax = fields.Monetary(
        string='Taxes',
        currency_field='currency_id',
        store=True,
        compute='_compute_amounts',
        help="Montant des taxes"
    )
    
    amount_total = fields.Monetary(
        string='Total',
        currency_field='currency_id',
        store=True,
        compute='_compute_amounts',
        tracking=True,
        help="Montant total TTC"
    )
    
    amount_paid = fields.Monetary(
        string='Montant payé',
        currency_field='currency_id',
        default=0.0,
        help="Montant déjà payé"
    )
    
    amount_residual = fields.Monetary(
        string='Montant restant',
        currency_field='currency_id',
        compute='_compute_payment_amounts',
        store=True,
        help="Montant restant à payer"
    )
    
    # Lignes de facture
    invoice_line_ids = fields.One2many(
        'edu.student.invoice.line',
        'invoice_id',
        string='Lignes de facture',
        help="Détail des éléments facturés"
    )
    
    # État et workflow
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('open', 'En cours'),
        ('paid', 'Payée'),
        ('partial', 'Partiellement payée'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True, help="État de la facture")
    
    payment_state = fields.Selection([
        ('not_paid', 'Non payée'),
        ('partial', 'Partiellement payée'),
        ('paid', 'Payée'),
        ('overpaid', 'Surpayée')
    ], string='État de paiement', compute='_compute_payment_state', store=True)
    
    # Configuration
    invoice_type = fields.Selection([
        ('tuition', 'Frais de scolarité'),
        ('registration', 'Frais d\'inscription'),
        ('transport', 'Transport'),
        ('meals', 'Restauration'),
        ('activities', 'Activités'),
        ('books', 'Manuels'),
        ('exams', 'Examens'),
        ('other', 'Autres')
    ], string='Type de facture', required=True, default='tuition')
    
    is_recurring = fields.Boolean(
        string='Facture récurrente',
        default=False,
        help="Facture générée automatiquement de façon récurrente"
    )
    
    recurring_period = fields.Selection([
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semester', 'Semestrielle'),
        ('annual', 'Annuelle')
    ], string='Période de récurrence')
    
    # Frais de retard
    late_fee_amount = fields.Monetary(
        string='Frais de retard',
        currency_field='currency_id',
        default=0.0,
        help="Montant des frais de retard appliqués"
    )
    
    late_fee_applied = fields.Boolean(
        string='Frais de retard appliqués',
        default=False
    )
    
    # Informations complémentaires
    notes = fields.Text(
        string='Notes internes',
        help="Notes internes non visibles sur la facture"
    )
    
    narration = fields.Text(
        string='Conditions de paiement',
        help="Conditions et modalités de paiement"
    )
    
    # Métadonnées
    user_id = fields.Many2one(
        'res.users',
        string='Commercial',
        default=lambda self: self.env.user,
        help="Utilisateur responsable de la facture"
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    # Facture comptable liée
    account_move_id = fields.Many2one(
        'account.move',
        string='Écriture comptable',
        copy=False,
        help="Écriture comptable générée automatiquement"
    )
    
    # Champs calculés pour les informations étudiant
    student_name = fields.Char(
        related='student_id.name',
        string='Nom de l\'étudiant',
        store=True
    )
    
    student_email = fields.Char(
        related='student_id.email',
        string='Email étudiant',
        store=True
    )
    
    student_phone = fields.Char(
        related='student_id.phone',
        string='Téléphone étudiant',
        store=True
    )
    
    @api.depends('student_id')
    def _compute_partner_id(self):
        """Calcule le partenaire responsable du paiement"""
        for record in self:
            if record.student_id and record.student_id.partner_id:
                record.partner_id = record.student_id.partner_id
            else:
                record.partner_id = False

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.price_tax')
    def _compute_amounts(self):
        """Calcule les montants de la facture"""
        for record in self:
            amount_untaxed = amount_tax = 0.0
            for line in record.invoice_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            record.amount_untaxed = amount_untaxed
            record.amount_tax = amount_tax
            record.amount_total = amount_untaxed + amount_tax

    @api.depends('amount_total', 'amount_paid')
    def _compute_payment_amounts(self):
        """Calcule les montants de paiement"""
        for record in self:
            record.amount_residual = record.amount_total - record.amount_paid

    @api.depends('amount_total', 'amount_paid')
    def _compute_payment_state(self):
        """Calcule l'état de paiement"""
        for record in self:
            if record.amount_paid == 0:
                record.payment_state = 'not_paid'
            elif record.amount_paid >= record.amount_total:
                record.payment_state = 'paid' if record.amount_paid == record.amount_total else 'overpaid'
            else:
                record.payment_state = 'partial'

    @api.constrains('due_date', 'invoice_date')
    def _check_dates(self):
        """Valide les dates"""
        for record in self:
            if record.due_date < record.invoice_date:
                raise ValidationError(_("La date d'échéance doit être postérieure à la date de facture."))

    @api.constrains('period_start', 'period_end')
    def _check_period(self):
        """Valide la période"""
        for record in self:
            if record.period_start and record.period_end and record.period_start > record.period_end:
                raise ValidationError(_("La date de fin de période doit être postérieure à la date de début."))

    def action_confirm(self):
        """Confirme la facture"""
        for record in self:
            if record.number == _('Nouveau'):
                record.number = self.env['ir.sequence'].next_by_code('edu.student.invoice') or _('Nouveau')
            record.state = 'open'

    def action_cancel(self):
        """Annule la facture"""
        for record in self:
            record.state = 'cancelled'

    def action_reset_to_draft(self):
        """Remet la facture en brouillon"""
        for record in self:
            record.state = 'draft'

    def action_register_payment(self):
        """Enregistre un paiement"""
        self.ensure_one()
        return {
            'name': _('Enregistrer un paiement'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'edu.student.invoice',
                'active_ids': self.ids,
                'default_amount': self.amount_residual,
            }
        }

    def action_send_invoice(self):
        """Envoie la facture par email"""
        self.ensure_one()
        template = self.env.ref('edu_accounting_pro.email_template_student_invoice', raise_if_not_found=False)
        if template:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mail.compose.message',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_model': 'edu.student.invoice',
                    'default_res_id': self.id,
                    'default_use_template': bool(template),
                    'default_template_id': template.id,
                    'default_composition_mode': 'comment',
                }
            }
        else:
            raise UserError(_("Aucun modèle d'email configuré pour les factures étudiants."))

    def action_duplicate(self):
        """Duplique la facture"""
        self.ensure_one()
        copy_vals = {
            'number': _('Nouveau'),
            'invoice_date': fields.Date.context_today(self),
            'due_date': fields.Date.context_today(self) + timedelta(days=30),
            'state': 'draft',
        }
        new_invoice = self.copy(copy_vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'edu.student.invoice',
            'res_id': new_invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        """Création d'une facture"""
        if vals.get('number', _('Nouveau')) == _('Nouveau'):
            vals['number'] = self.env['ir.sequence'].next_by_code('edu.student.invoice') or _('Nouveau')
        
        # Auto-compléter les informations de l'étudiant
        if vals.get('student_id') and not vals.get('course_id'):
            student = self.env['op.student'].browse(vals['student_id'])
            if student.course_detail_ids:
                course_detail = student.course_detail_ids[0]
                vals.update({
                    'course_id': course_detail.course_id.id,
                    'batch_id': course_detail.batch_id.id if course_detail.batch_id else False,
                    'academic_year_id': course_detail.academic_year_id.id,
                })
        
        return super().create(vals)

    def write(self, vals):
        """Mise à jour d'une facture"""
        # Mettre à jour l'état si nécessaire
        if 'amount_paid' in vals:
            for record in self:
                if vals['amount_paid'] >= record.amount_total:
                    vals['state'] = 'paid'
                elif vals['amount_paid'] > 0:
                    vals['state'] = 'partial'
                else:
                    vals['state'] = 'open'
        
        return super().write(vals)

    @api.model
    def _cron_update_overdue_invoices(self):
        """Tâche cron pour mettre à jour les factures en retard"""
        today = fields.Date.context_today(self)
        overdue_invoices = self.search([
            ('due_date', '<', today),
            ('state', '=', 'open'),
            ('amount_residual', '>', 0)
        ])
        overdue_invoices.write({'state': 'overdue'})
        _logger.info(f"Mise à jour de {len(overdue_invoices)} factures en retard")

    @api.model
    def _cron_send_payment_reminders(self):
        """Tâche cron pour envoyer des rappels de paiement"""
        today = fields.Date.context_today(self)
        reminder_date = today + timedelta(days=7)  # Rappel 7 jours avant échéance
        
        invoices_to_remind = self.search([
            ('due_date', '=', reminder_date),
            ('state', '=', 'open'),
            ('amount_residual', '>', 0)
        ])
        
        for invoice in invoices_to_remind:
            invoice._send_payment_reminder()
        
        _logger.info(f"Envoi de {len(invoices_to_remind)} rappels de paiement")

    def _send_payment_reminder(self):
        """Envoie un rappel de paiement"""
        self.ensure_one()
        template = self.env.ref('edu_accounting_pro.email_template_payment_reminder', raise_if_not_found=False)
        if template and self.student_id.email:
            template.send_mail(self.id, force_send=True)


class EduStudentInvoiceLine(models.Model):
    """Lignes de facture étudiant"""
    _name = 'edu.student.invoice.line'
    _description = 'Ligne de facture étudiant'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage"
    )
    
    invoice_id = fields.Many2one(
        'edu.student.invoice',
        string='Facture',
        required=True,
        ondelete='cascade'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Produit/Service',
        help="Produit ou service facturé"
    )
    
    description = fields.Text(
        string='Description',
        required=True,
        help="Description de l'élément facturé"
    )
    
    quantity = fields.Float(
        string='Quantité',
        default=1.0,
        digits='Product Unit of Measure',
        help="Quantité facturée"
    )
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unité de mesure',
        help="Unité de mesure"
    )
    
    price_unit = fields.Float(
        string='Prix unitaire',
        digits='Product Price',
        help="Prix unitaire"
    )
    
    price_subtotal = fields.Monetary(
        string='Sous-total',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help="Montant hors taxes"
    )
    
    price_tax = fields.Monetary(
        string='Taxes',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help="Montant des taxes"
    )
    
    price_total = fields.Monetary(
        string='Total',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help="Montant TTC"
    )
    
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        help="Taxes appliquées"
    )
    
    currency_id = fields.Many2one(
        related='invoice_id.currency_id',
        store=True
    )
    
    # Types spécifiques à l'éducation
    fee_type_id = fields.Many2one(
        'edu.fee.type',
        string='Type de frais',
        help="Type de frais éducatif"
    )
    
    academic_period = fields.Char(
        string='Période académique',
        help="Période académique concernée"
    )

    @api.depends('quantity', 'price_unit', 'tax_ids')
    def _compute_amounts(self):
        """Calcule les montants de la ligne"""
        for line in self:
            price = line.price_unit * line.quantity
            taxes = line.tax_ids.compute_all(
                price, line.currency_id, 1, product=line.product_id, partner=line.invoice_id.partner_id
            )
            line.price_subtotal = taxes['total_excluded']
            line.price_tax = taxes['total_included'] - taxes['total_excluded']
            line.price_total = taxes['total_included']

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Met à jour les informations lors du changement de produit"""
        if self.product_id:
            self.description = self.product_id.name
            self.price_unit = self.product_id.list_price
            self.uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.taxes_id
