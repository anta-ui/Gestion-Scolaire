# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduFeeType(models.Model):
    """Types de frais scolaires"""
    _name = 'edu.fee.type'
    _description = 'Type de Frais Scolaire'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du type de frais',
        required=True,
        translate=True,
        help="Nom du type de frais"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        help="Code unique du type de frais"
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Type de frais actif"
    )
    
    # Catégorisation
    category = fields.Selection([
        ('tuition', 'Frais de scolarité'),
        ('registration', 'Frais d\'inscription'),
        ('transport', 'Transport'),
        ('meals', 'Restauration'),
        ('accommodation', 'Hébergement'),
        ('activities', 'Activités extrascolaires'),
        ('books', 'Manuels et fournitures'),
        ('exams', 'Examens et certifications'),
        ('insurance', 'Assurance'),
        ('technology', 'Technologie et équipement'),
        ('uniform', 'Uniformes'),
        ('library', 'Bibliothèque'),
        ('laboratory', 'Laboratoire'),
        ('sports', 'Sports'),
        ('medical', 'Médical'),
        ('other', 'Autres')
    ], string='Catégorie', required=True, default='tuition',
       help="Catégorie du type de frais")
    
    # Configuration
    is_mandatory = fields.Boolean(
        string='Obligatoire par défaut',
        default=True,
        help="Ce type de frais est obligatoire par défaut"
    )
    
    is_refundable = fields.Boolean(
        string='Remboursable',
        default=False,
        help="Ce type de frais peut être remboursé"
    )
    
    allow_partial_payment = fields.Boolean(
        string='Paiement partiel autorisé',
        default=True,
        help="Autoriser les paiements partiels pour ce type"
    )
    
    # Comptabilité
    account_id = fields.Many2one(
        'account.account',
        string='Compte comptable',
        domain="[('account_type', '=', 'income')]",
        help="Compte de produits par défaut"
    )
    
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes par défaut',
        help="Taxes appliquées par défaut"
    )
    
    # Configuration des paiements
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Conditions de paiement',
        help="Conditions de paiement par défaut"
    )
    
    # Bourses et remises
    scholarship_applicable = fields.Boolean(
        string='Bourses applicables',
        default=True,
        help="Les bourses peuvent s'appliquer à ce type de frais"
    )
    
    discount_applicable = fields.Boolean(
        string='Remises applicables',
        default=True,
        help="Les remises peuvent s'appliquer à ce type de frais"
    )
    
    max_discount_percentage = fields.Float(
        string='Remise maximale (%)',
        default=100.0,
        digits=(5, 2),
        help="Pourcentage de remise maximale autorisée"
    )
    
    # Informations complémentaires
    description = fields.Html(
        string='Description',
        help="Description détaillée du type de frais"
    )
    
    notes = fields.Text(
        string='Notes internes',
        help="Notes internes pour ce type de frais"
    )
    
    # Produit associé
    product_id = fields.Many2one(
        'product.product',
        string='Produit associé',
        help="Produit Odoo associé à ce type de frais"
    )
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    # Statistiques calculées
    usage_count = fields.Integer(
        string='Nombre d\'utilisations',
        compute='_compute_usage_statistics',
        help="Nombre de fois que ce type de frais a été utilisé"
    )
    
    total_amount_invoiced = fields.Monetary(
        string='Montant total facturé',
        currency_field='currency_id',
        compute='_compute_usage_statistics',
        help="Montant total facturé pour ce type"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id
    )
    
    @api.depends('name')
    def _compute_usage_statistics(self):
        """Calcule les statistiques d'utilisation"""
        for record in self:
            # Nombre d'utilisations dans les lignes de facture
            usage_count = self.env['edu.student.invoice.line'].search_count([
                ('fee_type_id', '=', record.id)
            ])
            record.usage_count = usage_count
            
            # Montant total facturé
            lines = self.env['edu.student.invoice.line'].search([
                ('fee_type_id', '=', record.id)
            ])
            record.total_amount_invoiced = sum(lines.mapped('price_total'))
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            existing = self.search([
                ('code', '=', record.code),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_("Le code doit être unique par société."))
    
    @api.constrains('max_discount_percentage')
    def _check_discount_percentage(self):
        """Vérifie le pourcentage de remise"""
        for record in self:
            if record.max_discount_percentage < 0 or record.max_discount_percentage > 100:
                raise ValidationError(_("Le pourcentage de remise doit être entre 0 et 100."))
    
    @api.onchange('category')
    def _onchange_category(self):
        """Met à jour les valeurs par défaut selon la catégorie"""
        category_defaults = {
            'tuition': {
                'is_mandatory': True,
                'is_refundable': False,
                'allow_partial_payment': True,
                'scholarship_applicable': True,
            },
            'registration': {
                'is_mandatory': True,
                'is_refundable': False,
                'allow_partial_payment': False,
                'scholarship_applicable': False,
            },
            'transport': {
                'is_mandatory': False,
                'is_refundable': True,
                'allow_partial_payment': True,
                'scholarship_applicable': True,
            },
            'meals': {
                'is_mandatory': False,
                'is_refundable': True,
                'allow_partial_payment': True,
                'scholarship_applicable': True,
            },
            'activities': {
                'is_mandatory': False,
                'is_refundable': True,
                'allow_partial_payment': True,
                'scholarship_applicable': False,
            }
        }
        
        if self.category in category_defaults:
            defaults = category_defaults[self.category]
            for field, value in defaults.items():
                setattr(self, field, value)
    
    def action_create_product(self):
        """Crée un produit Odoo associé à ce type de frais"""
        self.ensure_one()
        
        if self.product_id:
            raise ValidationError(_("Un produit est déjà associé à ce type de frais."))
        
        product_vals = {
            'name': self.name,
            'default_code': self.code,
            'type': 'service',
            'invoice_policy': 'order',
            'taxes_id': [(6, 0, self.tax_ids.ids)],
            'categ_id': self._get_product_category().id,
            'description': self.description,
        }
        
        if self.account_id:
            product_vals['property_account_income_id'] = self.account_id.id
        
        product = self.env['product.product'].create(product_vals)
        self.product_id = product.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Produit créé'),
                'message': _('Le produit "%s" a été créé avec succès.') % product.name,
                'type': 'success',
            }
        }
    
    def _get_product_category(self):
        """Retourne la catégorie de produit appropriée"""
        category_mapping = {
            'tuition': 'Frais de Scolarité',
            'registration': 'Frais d\'Inscription',
            'transport': 'Transport Scolaire',
            'meals': 'Restauration',
            'accommodation': 'Hébergement',
            'activities': 'Activités',
            'books': 'Fournitures',
            'exams': 'Examens',
            'other': 'Services Éducatifs'
        }
        
        category_name = category_mapping.get(self.category, 'Services Éducatifs')
        
        # Chercher ou créer la catégorie
        category = self.env['product.category'].search([
            ('name', '=', category_name)
        ], limit=1)
        
        if not category:
            category = self.env['product.category'].create({
                'name': category_name,
                'parent_id': self.env['product.category'].search([
                    ('name', '=', 'Services')
                ], limit=1).id or False
            })
        
        return category
    
    def action_view_invoices(self):
        """Affiche les factures utilisant ce type de frais"""
        self.ensure_one()
        
        invoice_lines = self.env['edu.student.invoice.line'].search([
            ('fee_type_id', '=', self.id)
        ])
        invoice_ids = invoice_lines.mapped('invoice_id').ids
        
        return {
            'name': _('Factures - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'edu.student.invoice',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'default_fee_type_id': self.id}
        }
