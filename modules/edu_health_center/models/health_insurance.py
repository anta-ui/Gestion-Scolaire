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
        'company_id',
        string='Polices'
    )
    
    # Métadonnées
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )


class HealthInsurancePolicy(models.Model):
    """Polices d'assurance santé"""
    _name = 'health.insurance.policy'
    _description = 'Police d\'Assurance Santé'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'student_id, policy_number'

    name = fields.Char(
        string='Référence police',
        compute='_compute_name',
        store=True
    )
    
    # Relations
    student_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True,
        tracking=True
    )
    
    company_id = fields.Many2one(
        'health.insurance.company',
        string='Compagnie d\'assurance',
        required=True,
        tracking=True
    )
    
    # Informations de la police
    policy_number = fields.Char(
        string='Numéro de police',
        required=True,
        tracking=True
    )
    
    policy_holder = fields.Char(
        string='Titulaire de la police',
        help="Nom du titulaire (parent pour les mineurs)"
    )
    
    # Dates de couverture
    start_date = fields.Date(
        string='Date de début',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    end_date = fields.Date(
        string='Date de fin',
        required=True,
        tracking=True
    )
    
    # Couverture
    coverage_type = fields.Selection([
        ('basic', 'Couverture de base'),
        ('extended', 'Couverture étendue'),
        ('premium', 'Couverture premium'),
        ('comprehensive', 'Couverture complète')
    ], string='Type de couverture', required=True, default='basic')
    
    coverage_amount = fields.Float(
        string='Montant de couverture',
        help="Montant maximum de couverture"
    )
    
    deductible = fields.Float(
        string='Franchise',
        help="Montant de la franchise"
    )
    
    copayment_percentage = fields.Float(
        string='Pourcentage de participation',
        default=20.0,
        help="Pourcentage à la charge de l'assuré"
    )
    
    # Services couverts
    medical_consultations = fields.Boolean(
        string='Consultations médicales',
        default=True
    )
    
    emergency_care = fields.Boolean(
        string='Soins d\'urgence',
        default=True
    )
    
    prescription_drugs = fields.Boolean(
        string='Médicaments sur ordonnance',
        default=True
    )
    
    dental_care = fields.Boolean(
        string='Soins dentaires',
        default=False
    )
    
    vision_care = fields.Boolean(
        string='Soins de la vue',
        default=False
    )
    
    mental_health = fields.Boolean(
        string='Santé mentale',
        default=False
    )
    
    # État
    state = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspendue'),
        ('expired', 'Expirée'),
        ('cancelled', 'Annulée')
    ], string='État', default='active', tracking=True)
    
    # Relations
    claim_ids = fields.One2many(
        'health.insurance.claim',
        'policy_id',
        string='Réclamations'
    )
    
    # Statistiques
    total_claims = fields.Integer(
        string='Nombre de réclamations',
        compute='_compute_claim_stats'
    )
    
    total_claimed_amount = fields.Float(
        string='Montant total réclamé',
        compute='_compute_claim_stats'
    )
    
    total_reimbursed_amount = fields.Float(
        string='Montant total remboursé',
        compute='_compute_claim_stats'
    )
    
    @api.depends('student_id.name', 'policy_number')
    def _compute_name(self):
        """Calculer le nom de la police"""
        for policy in self:
            if policy.student_id and policy.policy_number:
                policy.name = f"{policy.student_id.name} - {policy.policy_number}"
            else:
                policy.name = policy.policy_number or 'Nouvelle police'
    
    @api.depends('claim_ids.amount_claimed', 'claim_ids.amount_reimbursed')
    def _compute_claim_stats(self):
        """Calculer les statistiques des réclamations"""
        for policy in self:
            policy.total_claims = len(policy.claim_ids)
            policy.total_claimed_amount = sum(policy.claim_ids.mapped('amount_claimed'))
            policy.total_reimbursed_amount = sum(policy.claim_ids.mapped('amount_reimbursed'))
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Vérifier la cohérence des dates"""
        for policy in self:
            if policy.start_date >= policy.end_date:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début."))
    
    def action_suspend(self):
        """Suspendre la police"""
        self.state = 'suspended'
    
    def action_reactivate(self):
        """Réactiver la police"""
        self.state = 'active'
    
    def action_cancel(self):
        """Annuler la police"""
        self.state = 'cancelled'


class HealthInsuranceClaim(models.Model):
    """Réclamations d'assurance"""
    _name = 'health.insurance.claim'
    _description = 'Réclamation d\'Assurance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'claim_date desc'

    name = fields.Char(
        string='Numéro de réclamation',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau'),
        help="Numéro unique de la réclamation"
    )
    
    # Relations
    policy_id = fields.Many2one(
        'health.insurance.policy',
        string='Police d\'assurance',
        required=True,
        tracking=True
    )
    
    student_id = fields.Many2one(
        related='policy_id.student_id',
        string='Étudiant',
        store=True
    )
    
    consultation_id = fields.Many2one(
        'edu.medical.consultation',
        string='Consultation',
        help="Consultation liée à la réclamation"
    )
    
    # Informations de la réclamation
    claim_date = fields.Date(
        string='Date de réclamation',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    service_date = fields.Date(
        string='Date du service',
        required=True,
        help="Date à laquelle le service médical a été fourni"
    )
    
    provider_name = fields.Char(
        string='Nom du prestataire',
        required=True,
        help="Nom du médecin ou de l'établissement"
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
        required=True,
        help="Description détaillée du service"
    )
    
    # Montants
    amount_claimed = fields.Float(
        string='Montant réclamé',
        required=True,
        tracking=True
    )
    
    amount_approved = fields.Float(
        string='Montant approuvé',
        tracking=True
    )
    
    amount_reimbursed = fields.Float(
        string='Montant remboursé',
        tracking=True
    )
    
    copayment = fields.Float(
        string='Participation',
        help="Montant à la charge de l'assuré"
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
    ], string='État', default='draft', tracking=True)
    
    # Dates de traitement
    submission_date = fields.Date(
        string='Date de soumission',
        tracking=True
    )
    
    review_date = fields.Date(
        string='Date d\'examen',
        tracking=True
    )
    
    approval_date = fields.Date(
        string='Date d\'approbation',
        tracking=True
    )
    
    payment_date = fields.Date(
        string='Date de paiement',
        tracking=True
    )
    
    # Motif de rejet
    rejection_reason = fields.Text(
        string='Motif de rejet',
        help="Raison du rejet de la réclamation"
    )
    
    # Documents
    supporting_documents = fields.Many2many(
        'ir.attachment',
        'claim_document_rel',
        'claim_id',
        'attachment_id',
        string='Documents justificatifs'
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
