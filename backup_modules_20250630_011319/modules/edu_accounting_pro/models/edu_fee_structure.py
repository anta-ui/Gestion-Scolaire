# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class EduFeeStructure(models.Model):
    """Structure des frais scolaires"""
    _name = 'edu.fee.structure'
    _description = 'Structure des Frais Scolaires'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'academic_year_id desc, course_id, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de la structure',
        required=True,
        tracking=True,
        help="Nom de la structure de frais"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        help="Code unique de la structure"
    )
    
    # Relations principales avec OpenEduCat
    academic_year_id = fields.Many2one(
        'op.academic.year',
        string='Année scolaire',
        required=True,
        tracking=True,
        help="Année scolaire concernée"
    )
    
    course_id = fields.Many2one(
        'op.course',
        string='Cours',
        required=True,
        tracking=True,
        help="Cours concerné par cette structure"
    )
    
    batch_id = fields.Many2one(
        'op.batch',
        string='Batch',
        tracking=True,
        help="Batch spécifique (optionnel)"
    )
    
    # Configuration
    active = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
        help="Structure active"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Devise des montants"
    )
    
    # Dates de validité
    date_start = fields.Date(
        string='Date de début',
        required=True,
        default=fields.Date.context_today,
        help="Date de début de validité"
    )
    
    date_end = fields.Date(
        string='Date de fin',
        help="Date de fin de validité"
    )
    
    # Types de facturation
    billing_type = fields.Selection([
        ('annual', 'Annuelle'),
        ('semester', 'Semestrielle'),
        ('quarterly', 'Trimestrielle'),
        ('monthly', 'Mensuelle'),
        ('custom', 'Personnalisée')
    ], string='Type de facturation', required=True, default='quarterly',
       tracking=True, help="Fréquence de facturation")
    
    # Lignes de frais
    fee_line_ids = fields.One2many(
        'edu.fee.structure.line',
        'fee_structure_id',
        string='Lignes de frais',
        help="Détail des frais inclus dans cette structure"
    )
    
    # Montants calculés
    total_amount = fields.Monetary(
        string='Montant total',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help="Montant total de la structure"
    )
    
    mandatory_amount = fields.Monetary(
        string='Montant obligatoire',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help="Montant des frais obligatoires"
    )
    
    optional_amount = fields.Monetary(
        string='Montant optionnel',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help="Montant des frais optionnels"
    )
    
    # Configuration des paiements
    allow_partial_payment = fields.Boolean(
        string='Paiement partiel autorisé',
        default=True,
        help="Autoriser les paiements partiels"
    )
    
    # Remises et bourses
    scholarship_applicable = fields.Boolean(
        string='Bourses applicables',
        default=True,
        help="Les bourses peuvent s'appliquer à cette structure"
    )
    
    discount_applicable = fields.Boolean(
        string='Remises applicables',
        default=True,
        help="Les remises peuvent s'appliquer à cette structure"
    )
    
    # Informations complémentaires
    description = fields.Html(
        string='Description',
        help="Description détaillée de la structure de frais"
    )
    
    notes = fields.Text(
        string='Notes internes',
        help="Notes internes pour cette structure"
    )
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    # Statistiques
    student_count = fields.Integer(
        string='Nombre d\'étudiants',
        compute='_compute_statistics',
        help="Nombre d'étudiants utilisant cette structure"
    )
    
    invoice_count = fields.Integer(
        string='Nombre de factures',
        compute='_compute_statistics',
        help="Nombre de factures générées"
    )
    
    @api.depends('fee_line_ids.amount', 'fee_line_ids.is_mandatory')
    def _compute_amounts(self):
        """Calcule les montants totaux"""
        for record in self:
            total = mandatory = optional = 0.0
            for line in record.fee_line_ids:
                total += line.amount
                if line.is_mandatory:
                    mandatory += line.amount
                else:
                    optional += line.amount
            
            record.total_amount = total
            record.mandatory_amount = mandatory
            record.optional_amount = optional
    
    def _compute_statistics(self):
        """Calcule les statistiques"""
        for record in self:
            # Compter les étudiants utilisant cette structure
            students = self.env['op.student'].search([
                ('course_detail_ids.course_id', '=', record.course_id.id),
                ('course_detail_ids.academic_year_id', '=', record.academic_year_id.id)
            ])
            if record.batch_id:
                students = students.filtered(lambda s: record.batch_id.id in s.course_detail_ids.mapped('batch_id.id'))
            
            record.student_count = len(students)
            
            # Compter les factures générées
            invoices = self.env['edu.student.invoice'].search([
                ('course_id', '=', record.course_id.id),
                ('academic_year_id', '=', record.academic_year_id.id)
            ])
            if record.batch_id:
                invoices = invoices.filtered(lambda i: i.batch_id.id == record.batch_id.id)
            
            record.invoice_count = len(invoices)
    
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """Valide les dates"""
        for record in self:
            if record.date_end and record.date_start > record.date_end:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début."))
    
    @api.constrains('code', 'academic_year_id', 'course_id')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            domain = [
                ('code', '=', record.code),
                ('academic_year_id', '=', record.academic_year_id.id),
                ('course_id', '=', record.course_id.id),
                ('id', '!=', record.id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(
                    _("Le code '%s' existe déjà pour cette année scolaire et ce cours.") % record.code
                )
    
    def action_generate_invoices(self):
        """Génère les factures pour tous les étudiants éligibles"""
        self.ensure_one()
        
        # Rechercher les étudiants éligibles
        domain = [
            ('course_detail_ids.course_id', '=', self.course_id.id),
            ('course_detail_ids.academic_year_id', '=', self.academic_year_id.id)
        ]
        
        students = self.env['op.student'].search(domain)
        
        if self.batch_id:
            students = students.filtered(
                lambda s: self.batch_id.id in s.course_detail_ids.mapped('batch_id.id')
            )
        
        invoices_created = 0
        for student in students:
            # Vérifier si une facture n'existe pas déjà
            existing_invoice = self.env['edu.student.invoice'].search([
                ('student_id', '=', student.id),
                ('course_id', '=', self.course_id.id),
                ('academic_year_id', '=', self.academic_year_id.id),
                ('state', '!=', 'cancelled')
            ], limit=1)
            
            if not existing_invoice:
                self._create_invoice_for_student(student)
                invoices_created += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Factures générées'),
                'message': _('%d factures ont été créées avec succès.') % invoices_created,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _create_invoice_for_student(self, student):
        """Crée une facture pour un étudiant"""
        invoice_vals = {
            'student_id': student.id,
            'course_id': self.course_id.id,
            'batch_id': self.batch_id.id if self.batch_id else False,
            'academic_year_id': self.academic_year_id.id,
            'invoice_date': fields.Date.context_today(self),
            'due_date': self._calculate_due_date(),
            'invoice_type': 'tuition',
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
        }
        
        invoice = self.env['edu.student.invoice'].create(invoice_vals)
        
        # Créer les lignes de facture
        for line in self.fee_line_ids:
            invoice_line_vals = {
                'invoice_id': invoice.id,
                'description': line.fee_type_id.name,
                'quantity': 1.0,
                'price_unit': line.amount,
                'fee_type_id': line.fee_type_id.id,
                'tax_ids': [(6, 0, line.tax_ids.ids)],
            }
            self.env['edu.student.invoice.line'].create(invoice_line_vals)
        
        return invoice
    
    def _calculate_due_date(self):
        """Calcule la date d'échéance"""
        return fields.Date.context_today(self) + timedelta(days=30)
    
    def action_view_invoices(self):
        """Affiche les factures liées à cette structure"""
        self.ensure_one()
        
        domain = [
            ('course_id', '=', self.course_id.id),
            ('academic_year_id', '=', self.academic_year_id.id)
        ]
        
        if self.batch_id:
            domain.append(('batch_id', '=', self.batch_id.id))
        
        return {
            'name': _('Factures - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'edu.student.invoice',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_course_id': self.course_id.id},
        }
    
    def action_duplicate(self):
        """Duplique la structure de frais"""
        self.ensure_one()
        
        new_name = _("Copie de %s") % self.name
        new_code = "%s_copy" % self.code
        
        # S'assurer que le nouveau code est unique
        counter = 1
        while self.search([('code', '=', new_code)]):
            new_code = "%s_copy_%d" % (self.code, counter)
            counter += 1
        
        copy_vals = {
            'name': new_name,
            'code': new_code,
        }
        
        new_structure = self.copy(copy_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'edu.fee.structure',
            'res_id': new_structure.id,
            'view_mode': 'form',
            'target': 'current',
        }


class EduFeeStructureLine(models.Model):
    """Ligne de structure de frais"""
    _name = 'edu.fee.structure.line'
    _description = 'Ligne de Structure de Frais'
    _order = 'sequence, fee_type_id'

    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage"
    )
    
    fee_structure_id = fields.Many2one(
        'edu.fee.structure',
        string='Structure de frais',
        required=True,
        ondelete='cascade'
    )
    
    fee_type_id = fields.Many2one(
        'edu.fee.type',
        string='Type de frais',
        required=True,
        help="Type de frais"
    )
    
    amount = fields.Monetary(
        string='Montant',
        currency_field='currency_id',
        required=True,
        help="Montant du frais"
    )
    
    currency_id = fields.Many2one(
        related='fee_structure_id.currency_id',
        store=True
    )
    
    is_mandatory = fields.Boolean(
        string='Obligatoire',
        default=True,
        help="Frais obligatoire"
    )
    
    description = fields.Text(
        string='Description',
        help="Description du frais"
    )
    
    # Configuration des taxes
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        help="Taxes applicables"
    )
    
    # Compte comptable
    account_id = fields.Many2one(
        'account.account',
        string='Compte comptable',
        help="Compte comptable pour ce type de frais"
    )
    
    @api.constrains('amount')
    def _check_amount(self):
        """Valide le montant"""
        for record in self:
            if record.amount < 0:
                raise ValidationError(_("Le montant ne peut pas être négatif."))
