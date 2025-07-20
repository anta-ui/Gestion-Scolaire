# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MedicationStock(models.Model):
    """Gestion du stock de médicaments"""
    _name = 'medication.stock'
    _description = 'Stock de Médicaments'
    _order = 'medication_name'

    # Informations de base
    medication_name = fields.Char(
        string='Nom du médicament',
        required=True
    )

    active_ingredient = fields.Char(
        string='Principe actif'
    )

    dosage = fields.Char(
        string='Dosage'
    )

    form = fields.Selection([
        ('tablet', 'Comprimé'),
        ('capsule', 'Gélule'),
        ('liquid', 'Liquide'),
        ('injection', 'Injection'),
        ('cream', 'Crème'),
        ('drops', 'Gouttes'),
        ('inhaler', 'Inhalateur'),
        ('other', 'Autre'),
    ], string='Forme', required=True, default='tablet')

    # Stock
    quantity_on_hand = fields.Float(
        string='Quantité en stock',
        default=0.0
    )

    unit_of_measure = fields.Selection([
        ('unit', 'Unité'),
        ('box', 'Boîte'),
        ('bottle', 'Flacon'),
        ('ml', 'ml'),
        ('g', 'gramme'),
    ], string='Unité de mesure', default='unit')

    minimum_stock = fields.Float(
        string='Stock minimum',
        default=10.0
    )

    # Informations légales
    prescription_required = fields.Boolean(
        string='Prescription requise',
        default=True
    )

    controlled_substance = fields.Boolean(
        string='Substance contrôlée',
        default=False
    )

    # Dates
    expiry_date = fields.Date(
        string='Date d\'expiration'
    )

    # Coût
    unit_cost = fields.Float(
        string='Coût unitaire'
    )

    supplier = fields.Char(
        string='Fournisseur'
    )

    # État
    state = fields.Selection([
        ('available', 'Disponible'),
        ('low_stock', 'Stock faible'),
        ('out_of_stock', 'Rupture de stock'),
        ('expired', 'Expiré'),
    ], string='État', compute='_compute_state', store=True)

    @api.depends('quantity_on_hand', 'minimum_stock', 'expiry_date')
    def _compute_state(self):
        """Calculer l'état du stock"""
        today = fields.Date.today()
        for record in self:
            if record.expiry_date and record.expiry_date <= today:
                record.state = 'expired'
            elif record.quantity_on_hand <= 0:
                record.state = 'out_of_stock'
            elif record.quantity_on_hand <= record.minimum_stock:
                record.state = 'low_stock'
            else:
                record.state = 'available'


class MedicationPrescription(models.Model):
    """Prescriptions médicamenteuses"""
    _name = 'medication.prescription'
    _description = 'Prescription Médicamenteuse'
    _order = 'prescription_date desc'

    # Informations de base
    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )

    prescription_date = fields.Date(
        string='Date de prescription',
        required=True,
        default=fields.Date.today
    )

    # Patient et consultation
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        required=True
    )

    consultation_id = fields.Many2one(
        'edu.medical.consultation',
        string='Consultation'
    )

    # Médicament
    medication_id = fields.Many2one(
        'medication.stock',
        string='Médicament',
        required=True
    )

    # Posologie
    dosage_instructions = fields.Text(
        string='Instructions de dosage',
        required=True
    )

    quantity_prescribed = fields.Float(
        string='Quantité prescrite',
        required=True
    )

    duration_days = fields.Integer(
        string='Durée (jours)',
        required=True
    )

    # Médecin prescripteur
    prescribed_by = fields.Many2one(
        'res.users',
        string='Prescrit par',
        required=True,
        default=lambda self: self.env.user
    )

    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('prescribed', 'Prescrit'),
        ('dispensed', 'Délivré'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ], string='État', default='draft')

    # Actions
    def action_prescribe(self):
        """Prescrire le médicament"""
        self.state = 'prescribed'
        return True

    def action_dispense(self):
        """Délivrer le médicament"""
        self.state = 'dispensed'
        return True

    @api.model
    def create(self, vals):
        """Génération automatique du numéro de prescription"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medication.prescription') or _('Nouveau')
        return super().create(vals)


class MedicationAdministration(models.Model):
    """Administration de médicaments"""
    _name = 'medication.administration'
    _description = 'Administration de Médicament'
    _order = 'administration_date desc'

    # Informations de base
    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )

    administration_date = fields.Datetime(
        string='Date/Heure d\'administration',
        required=True,
        default=fields.Datetime.now
    )

    # Prescription associée
    prescription_id = fields.Many2one(
        'medication.prescription',
        string='Prescription',
        required=True
    )

    # Quantité administrée
    quantity_administered = fields.Float(
        string='Quantité administrée',
        required=True
    )

    # Personnel
    administered_by = fields.Many2one(
        'res.users',
        string='Administré par',
        required=True,
        default=lambda self: self.env.user
    )

    # Notes
    notes = fields.Text(
        string='Notes'
    )

    # Effets secondaires
    side_effects = fields.Text(
        string='Effets secondaires observés'
    )

    # État
    state = fields.Selection([
        ('planned', 'Planifié'),
        ('administered', 'Administré'),
        ('missed', 'Raté'),
        ('refused', 'Refusé'),
    ], string='État', default='planned')

    @api.model
    def create(self, vals):
        """Génération automatique du numéro d'administration"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medication.administration') or _('Nouveau')
        return super().create(vals)
