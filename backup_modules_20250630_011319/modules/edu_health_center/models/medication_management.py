# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MedicationStock(models.Model):
    """Stock de médicaments de l'infirmerie"""
    _name = 'medication.stock'
    _description = 'Stock de Médicaments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Nom du médicament',
        required=True,
        help="Nom commercial ou générique du médicament"
    )
    
    active_ingredient = fields.Char(
        string='Principe actif',
        help="Principe actif principal du médicament"
    )
    
    dosage = fields.Char(
        string='Dosage',
        help="Dosage du médicament (ex: 500mg, 10ml)"
    )
    
    form = fields.Selection([
        ('tablet', 'Comprimé'),
        ('capsule', 'Gélule'),
        ('syrup', 'Sirop'),
        ('injection', 'Injectable'),
        ('cream', 'Crème/Pommade'),
        ('drops', 'Gouttes'),
        ('spray', 'Spray'),
        ('other', 'Autre')
    ], string='Forme', required=True)
    
    # Stock
    current_stock = fields.Float(
        string='Stock actuel',
        default=0.0,
        help="Quantité actuellement en stock"
    )
    
    minimum_stock = fields.Float(
        string='Stock minimum',
        default=10.0,
        help="Seuil d'alerte pour le réapprovisionnement"
    )
    
    unit_of_measure = fields.Char(
        string='Unité de mesure',
        default='unité',
        help="Unité de mesure (unité, ml, g, etc.)"
    )
    
    # Dates importantes
    expiry_date = fields.Date(
        string='Date d\'expiration',
        help="Date d'expiration du lot actuel"
    )
    
    batch_number = fields.Char(
        string='Numéro de lot',
        help="Numéro de lot du médicament"
    )
    
    # Classification
    category = fields.Selection([
        ('analgesic', 'Antalgique'),
        ('antibiotic', 'Antibiotique'),
        ('antiseptic', 'Antiseptique'),
        ('antihistamine', 'Antihistaminique'),
        ('emergency', 'Urgence'),
        ('chronic', 'Traitement chronique'),
        ('other', 'Autre')
    ], string='Catégorie', required=True)
    
    prescription_required = fields.Boolean(
        string='Prescription requise',
        default=False,
        help="Ce médicament nécessite-t-il une prescription?"
    )
    
    # Alertes et restrictions
    allergy_warnings = fields.Text(
        string='Alertes allergies',
        help="Alertes concernant les allergies connues"
    )
    
    contraindications = fields.Text(
        string='Contre-indications',
        help="Contre-indications du médicament"
    )
    
    side_effects = fields.Text(
        string='Effets secondaires',
        help="Effets secondaires possibles"
    )
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    @api.constrains('current_stock', 'minimum_stock')
    def _check_stock_positive(self):
        """Vérifier que les stocks sont positifs"""
        for record in self:
            if record.current_stock < 0:
                raise ValidationError(_("Le stock actuel ne peut pas être négatif."))
            if record.minimum_stock < 0:
                raise ValidationError(_("Le stock minimum ne peut pas être négatif."))
    
    def action_replenish_stock(self):
        """Action pour réapprovisionner le stock"""
        return {
            'name': _('Réapprovisionner le stock'),
            'type': 'ir.actions.act_window',
            'res_model': 'medication.replenishment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_medication_id': self.id}
        }


class MedicationPrescription(models.Model):
    """Prescriptions de médicaments"""
    _name = 'medication.prescription'
    _description = 'Prescription de Médicament'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'prescription_date desc'

    name = fields.Char(
        string='Numéro de prescription',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau'),
        help="Numéro unique de la prescription"
    )
    
    # Relations
    student_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True,
        tracking=True,
        help="Étudiant concerné par la prescription"
    )
    
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        help="Dossier médical lié"
    )
    
    consultation_id = fields.Many2one(
        'edu.medical.consultation',
        string='Consultation',
        help="Consultation liée à cette prescription"
    )
    
    prescribed_by = fields.Many2one(
        'hr.employee',
        string='Prescrit par',
        required=True,
        help="Médecin ou infirmier qui a prescrit"
    )
    
    # Dates
    prescription_date = fields.Date(
        string='Date de prescription',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    
    start_date = fields.Date(
        string='Date de début',
        required=True,
        help="Date de début du traitement"
    )
    
    end_date = fields.Date(
        string='Date de fin',
        help="Date de fin du traitement (si applicable)"
    )
    
    # Médicament et posologie
    medication_id = fields.Many2one(
        'medication.stock',
        string='Médicament',
        required=True,
        help="Médicament prescrit"
    )
    
    dosage = fields.Char(
        string='Posologie',
        required=True,
        help="Posologie prescrite (ex: 1 comprimé 3 fois par jour)"
    )
    
    quantity_prescribed = fields.Float(
        string='Quantité prescrite',
        required=True,
        help="Quantité totale prescrite"
    )
    
    quantity_dispensed = fields.Float(
        string='Quantité délivrée',
        default=0.0,
        help="Quantité déjà délivrée"
    )
    
    # Instructions
    instructions = fields.Text(
        string='Instructions',
        help="Instructions spéciales pour la prise du médicament"
    )
    
    reason = fields.Text(
        string='Motif',
        required=True,
        help="Motif de la prescription"
    )
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Active'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    @api.model
    def create(self, vals):
        """Création d'une prescription"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medication.prescription') or _('Nouveau')
        return super().create(vals)
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Vérifier la cohérence des dates"""
        for record in self:
            if record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début."))
    
    def action_activate(self):
        """Activer la prescription"""
        self.state = 'active'
    
    def action_complete(self):
        """Marquer la prescription comme terminée"""
        self.state = 'completed'
    
    def action_cancel(self):
        """Annuler la prescription"""
        self.state = 'cancelled'


class MedicationDispensing(models.Model):
    """Distribution de médicaments"""
    _name = 'medication.dispensing'
    _description = 'Distribution de Médicament'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'dispensing_date desc'

    name = fields.Char(
        string='Numéro de distribution',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau'),
        help="Numéro unique de la distribution"
    )
    
    # Relations
    prescription_id = fields.Many2one(
        'medication.prescription',
        string='Prescription',
        required=True,
        help="Prescription liée"
    )
    
    student_id = fields.Many2one(
        related='prescription_id.student_id',
        string='Étudiant',
        store=True
    )
    
    medication_id = fields.Many2one(
        related='prescription_id.medication_id',
        string='Médicament',
        store=True
    )
    
    dispensed_by = fields.Many2one(
        'hr.employee',
        string='Distribué par',
        required=True,
        default=lambda self: self.env.user.employee_id,
        help="Personnel qui a distribué le médicament"
    )
    
    # Détails de la distribution
    dispensing_date = fields.Datetime(
        string='Date/Heure de distribution',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    
    quantity_dispensed = fields.Float(
        string='Quantité distribuée',
        required=True,
        help="Quantité distribuée lors de cette distribution"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Notes sur la distribution"
    )
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    @api.model
    def create(self, vals):
        """Création d'une distribution"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medication.dispensing') or _('Nouveau')
        
        # Mettre à jour le stock et la prescription
        if vals.get('prescription_id') and vals.get('quantity_dispensed'):
            prescription = self.env['medication.prescription'].browse(vals['prescription_id'])
            if prescription.medication_id:
                # Réduire le stock
                prescription.medication_id.current_stock -= vals['quantity_dispensed']
                # Mettre à jour la quantité délivrée dans la prescription
                prescription.quantity_dispensed += vals['quantity_dispensed']
        
        return super().create(vals)
    
    @api.constrains('quantity_dispensed')
    def _check_quantity_positive(self):
        """Vérifier que la quantité distribuée est positive"""
        for record in self:
            if record.quantity_dispensed <= 0:
                raise ValidationError(_("La quantité distribuée doit être positive."))
    
    @api.constrains('prescription_id', 'quantity_dispensed')
    def _check_prescription_quantity(self):
        """Vérifier que la quantité ne dépasse pas la prescription"""
        for record in self:
            total_dispensed = sum(record.prescription_id.dispensing_ids.mapped('quantity_dispensed'))
            if total_dispensed > record.prescription_id.quantity_prescribed:
                raise ValidationError(_("La quantité totale distribuée ne peut pas dépasser la quantité prescrite."))
