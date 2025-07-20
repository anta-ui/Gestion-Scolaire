# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HealthInsuranceCompany(models.Model):
    """Compagnies d'assurance santé"""
    _name = 'health.insurance.company'
    _description = 'Compagnie d\'Assurance Santé'
    _order = 'name'

    name = fields.Char(
        string='Nom de la compagnie',
        required=True,
        help="Nom de la compagnie d'assurance"
    )
    
    code = fields.Char(
        string='Code compagnie',
        help="Code unique de la compagnie"
    )
    
    # Informations de contact
    phone = fields.Char(string='Téléphone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Site web')
    
    # Adresse
    street = fields.Char(string='Rue')
    street2 = fields.Char(string='Rue 2')
    city = fields.Char(string='Ville')
    zip = fields.Char(string='Code postal')
    state_id = fields.Many2one('res.country.state', string='État')
    country_id = fields.Many2one('res.country', string='Pays')
    
    # Contact commercial
    contact_person = fields.Char(string='Personne de contact')
    contact_phone = fields.Char(string='Téléphone contact')
    contact_email = fields.Char(string='Email contact')
    
    # Informations commerciales
    contract_number = fields.Char(string='Numéro de contrat')
    coverage_percentage = fields.Float(
        string='Pourcentage de couverture',
        default=80.0,
        help="Pourcentage de couverture standard"
    )
    
    # Notes
    notes = fields.Text(string='Notes')
    
    # Relations
    policy_ids = fields.One2many(
        'health.insurance.policy',
        'insurance_company_id',
        string='Polices'
    )
    
    # Métadonnées
    active = fields.Boolean(default=True)
    # company_id = fields.Many2one(
    #     'res.company',
    #     string='Société',
    #     required=True,
    #     default=lambda self: self.env.company
    # )


class HealthInsurancePolicy(models.Model):
    """Polices d'assurance santé"""
    _name = 'health.insurance.policy'
    _description = 'Police d\'Assurance Santé'
    _order = 'policy_number'

    name = fields.Char(
        string='Nom de la police',
        required=True
    )
    
    policy_number = fields.Char(
        string='Numéro de police',
        required=True
    )
    
    # Compagnie d'assurance
    insurance_company_id = fields.Many2one(
        'health.insurance.company',
        string='Compagnie d\'assurance',
        required=True
    )
    
    # Patient assuré
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        required=True
    )
    
    student_id = fields.Many2one(
        related='health_record_id.student_id',
        string='Étudiant assuré',
        readonly=True,
        store=True
    )
    
    # Dates de validité
    start_date = fields.Date(
        string='Date de début',
        required=True
    )
    
    end_date = fields.Date(
        string='Date de fin',
        required=True
    )
    
    # Type de couverture
    coverage_type = fields.Selection([
        ('basic', 'Couverture de base'),
        ('standard', 'Couverture standard'),
        ('premium', 'Couverture premium'),
        ('comprehensive', 'Couverture complète'),
    ], string='Type de couverture', required=True, default='standard')
    
    # Limites financières
    annual_limit = fields.Float(
        string='Limite annuelle'
    )
    
    deductible = fields.Float(
        string='Franchise'
    )
    
    copayment_percentage = fields.Float(
        string='Pourcentage de participation (%)',
        default=20.0
    )
    
    # Services couverts
    emergency_covered = fields.Boolean(
        string='Urgences couvertes',
        default=True
    )
    
    consultation_covered = fields.Boolean(
        string='Consultations couvertes',
        default=True
    )
    
    medication_covered = fields.Boolean(
        string='Médicaments couverts',
        default=True
    )
    
    dental_covered = fields.Boolean(
        string='Soins dentaires couverts',
        default=False
    )
    
    optical_covered = fields.Boolean(
        string='Soins optiques couverts',
        default=False
    )
    
    # État
    state = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspendue'),
        ('expired', 'Expirée'),
        ('cancelled', 'Annulée'),
    ], string='État', default='active', compute='_compute_state', store=True)
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )
    
    # Contacts
    emergency_contact_number = fields.Char(
        string='Numéro d\'urgence assurance'
    )
    
    @api.depends('start_date', 'end_date')
    def _compute_state(self):
        """Calculer l'état de la police"""
        today = fields.Date.today()
        for record in self:
            if not record.start_date or not record.end_date:
                record.state = 'active'
            elif today < record.start_date:
                record.state = 'active'  # Future
            elif today > record.end_date:
                record.state = 'expired'
            else:
                record.state = 'active'
    
    def action_suspend(self):
        """Suspendre la police"""
        self.state = 'suspended'
        return True
    
    def action_cancel(self):
        """Annuler la police"""
        self.state = 'cancelled'
        return True
    
    def action_reactivate(self):
        """Réactiver la police"""
        self.state = 'active'
        return True


class HealthInsuranceClaim(models.Model):
    """Réclamations d'assurance"""
    _name = 'health.insurance.claim'
    _description = 'Réclamation d\'Assurance'
    _order = 'claim_date desc'

    name = fields.Char(
        string='Numéro de réclamation',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau')
    )
    
    # Relations
    policy_id = fields.Many2one(
        'health.insurance.policy',
        string='Police d\'assurance',
        required=True
    )
    
    student_id = fields.Many2one(
        related='policy_id.student_id',
        string='Étudiant',
        store=True
    )
    
    consultation_id = fields.Many2one(
        'edu.medical.consultation',
        string='Consultation'
    )
    
    # Informations de la réclamation
    claim_date = fields.Date(
        string='Date de réclamation',
        required=True,
        default=fields.Date.today
    )
    
    service_date = fields.Date(
        string='Date du service',
        required=True
    )
    
    provider_name = fields.Char(
        string='Nom du prestataire',
        required=True
    )
    
    service_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('emergency', 'Urgence'),
        ('medication', 'Médicaments'),
        ('lab_test', 'Analyses'),
        ('imaging', 'Imagerie'),
        ('dental', 'Soins dentaires'),
        ('vision', 'Soins de la vue'),
        ('other', 'Autre')
    ], string='Type de service', required=True)
    
    description = fields.Text(
        string='Description',
        required=True
    )
    
    # Montants
    amount_claimed = fields.Float(
        string='Montant réclamé',
        required=True
    )
    
    amount_approved = fields.Float(
        string='Montant approuvé'
    )
    
    amount_reimbursed = fields.Float(
        string='Montant remboursé'
    )
    
    copayment = fields.Float(
        string='Participation'
    )
    
    # État de la réclamation
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('under_review', 'En cours d\'examen'),
        ('approved', 'Approuvée'),
        ('partially_approved', 'Partiellement approuvée'),
        ('rejected', 'Rejetée'),
        ('paid', 'Payée')
    ], string='État', default='draft')
    
    # Dates de traitement
    submission_date = fields.Date(
        string='Date de soumission'
    )
    
    review_date = fields.Date(
        string='Date d\'examen'
    )
    
    approval_date = fields.Date(
        string='Date d\'approbation'
    )
    
    payment_date = fields.Date(
        string='Date de paiement'
    )
    
    # Motif de rejet
    rejection_reason = fields.Text(
        string='Motif de rejet'
    )
    
    # Notes
    notes = fields.Text(string='Notes')
    
    @api.model
    def create(self, vals):
        """Création d'une réclamation"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('health.insurance.claim') or _('Nouveau')
        return super().create(vals)
    
    def action_submit(self):
        """Soumettre la réclamation"""
        self.write({
            'state': 'submitted',
            'submission_date': fields.Date.today()
        })
    
    def action_review(self):
        """Mettre en cours d'examen"""
        self.write({
            'state': 'under_review',
            'review_date': fields.Date.today()
        })
    
    def action_approve(self):
        """Approuver la réclamation"""
        self.write({
            'state': 'approved',
            'approval_date': fields.Date.today(),
            'amount_approved': self.amount_claimed
        })
    
    def action_partially_approve(self):
        """Approuver partiellement"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Approbation partielle'),
            'res_model': 'health.insurance.partial.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_claim_id': self.id}
        }
    
    def action_reject(self):
        """Rejeter la réclamation"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rejeter la réclamation'),
            'res_model': 'health.insurance.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_claim_id': self.id}
        }
    
    def action_mark_paid(self):
        """Marquer comme payée"""
        self.write({
            'state': 'paid',
            'payment_date': fields.Date.today(),
            'amount_reimbursed': self.amount_approved
        })
