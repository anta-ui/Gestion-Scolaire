# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StudentFamilyGroup(models.Model):
    """Groupes familiaux pour gérer les fratries"""
    _name = 'student.family.group'
    _description = 'Groupe Familial'
    _rec_name = 'family_name'
    
    family_name = fields.Char('Nom de Famille', required=True)
    family_code = fields.Char('Code Famille', required=True)
    
    # Relations
    student_ids = fields.One2many('op.student', 'family_group_id', string='Enfants')
    parent_ids = fields.Many2many('op.parent', 'family_parent_rel', 'family_id', 'parent_id', string='Parents')
    
    # Informations familiales
    home_address = fields.Text('Adresse Familiale')
    home_phone = fields.Char('Téléphone Fixe')
    family_income = fields.Selection([
        ('very_low', 'Très Faible (< 100k)'),
        ('low', 'Faible (100k - 300k)'),
        ('medium', 'Moyen (300k - 600k)'),
        ('high', 'Élevé (600k - 1M)'),
        ('very_high', 'Très Élevé (> 1M)')
    ], string='Niveau de Revenus (FCFA/mois)')
    
    family_size = fields.Integer('Taille de la Famille', compute='_compute_family_size')
    children_count = fields.Integer('Nombre d\'Enfants', compute='_compute_children_count')
    
    # Contacts d'urgence
    emergency_contact_name = fields.Char('Contact d\'Urgence')
    emergency_contact_phone = fields.Char('Téléphone d\'Urgence')
    emergency_contact_relation = fields.Char('Lien de Parenté')
    
    # Informations socio-économiques
    housing_type = fields.Selection([
        ('owned', 'Propriétaire'),
        ('rented', 'Locataire'),
        ('family_house', 'Maison Familiale'),
        ('social_housing', 'Logement Social'),
        ('other', 'Autre')
    ], string='Type de Logement')
    
    transportation_mode = fields.Selection([
        ('walking', 'À Pied'),
        ('bicycle', 'Vélo'),
        ('motorcycle', 'Moto'),
        ('car', 'Voiture'),
        ('public_transport', 'Transport Public'),
        ('school_bus', 'Bus Scolaire'),
        ('mixed', 'Mixte')
    ], string='Mode de Transport')
    
    # Besoins spéciaux familiaux
    special_circumstances = fields.Text('Circonstances Particulières')
    financial_assistance_needed = fields.Boolean('Aide Financière Nécessaire')
    social_services_involved = fields.Boolean('Services Sociaux Impliqués')
    
    # Préférences
    preferred_language = fields.Selection([
        ('french', 'Français'),
        ('wolof', 'Wolof'),
        ('pulaar', 'Pulaar'),
        ('serer', 'Serer'),
        ('diola', 'Diola'),
        ('mandinka', 'Mandinka'),
        ('other', 'Autre')
    ], string='Langue Préférée', default='french')
    
    communication_preference = fields.Selection([
        ('phone', 'Téléphone'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('visit', 'Visite à Domicile')
    ], string='Préférence Communication', default='phone')
    
    # Métadonnées
    notes = fields.Text('Notes Familiales')
    created_date = fields.Datetime('Date de Création', default=fields.Datetime.now)
    last_contact_date = fields.Date('Dernier Contact')
    
    # Champs calculés
    total_fees_due = fields.Float('Total Frais Dus', compute='_compute_financial_summary')
    total_fees_paid = fields.Float('Total Frais Payés', compute='_compute_financial_summary')
    family_discount_rate = fields.Float('Taux Remise Famille (%)', default=0.0)
    
    @api.depends('student_ids', 'parent_ids')
    def _compute_family_size(self):
        """Calculer la taille de la famille"""
        for family in self:
            family.family_size = len(family.student_ids) + len(family.parent_ids)
    
    @api.depends('student_ids')
    def _compute_children_count(self):
        """Calculer le nombre d'enfants"""
        for family in self:
            family.children_count = len(family.student_ids)
    
    def _compute_financial_summary(self):
        """Calculer le résumé financier familial"""
        for family in self:
            # Logique pour calculer les frais dus et payés
            # À implémenter avec le module de comptabilité
            family.total_fees_due = 0.0
            family.total_fees_paid = 0.0
    
    @api.constrains('family_discount_rate')
    def _check_discount_rate(self):
        """Valider le taux de remise"""
        for family in self:
            if family.family_discount_rate < 0 or family.family_discount_rate > 100:
                raise ValidationError(_("Le taux de remise doit être entre 0 et 100%."))
    
    def action_view_children(self):
        """Voir tous les enfants de la famille"""
        return {
            'name': f'Enfants - Famille {self.family_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'op.student',
            'view_mode': 'tree,form',
            'domain': [('family_group_id', '=', self.id)],
            'context': {'default_family_group_id': self.id}
        }
    
    def action_family_meeting(self):
        """Programmer une réunion familiale"""
        return {
            'name': 'Programmer Réunion Familiale',
            'type': 'ir.actions.act_window',
            'res_model': 'family.meeting.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_family_id': self.id}
        }
    
    def action_send_family_communication(self):
        """Envoyer une communication à toute la famille"""
        return {
            'name': 'Communication Familiale',
            'type': 'ir.actions.act_window',
            'res_model': 'family.communication.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_family_id': self.id}
        }

class StudentGuardian(models.Model):
    """Tuteurs et gardiens des élèves"""
    _name = 'student.guardian'
    _description = 'Tuteur/Gardien'
    _rec_name = 'name'
    
    student_id = fields.Many2one('op.student', string='Élève', required=True, ondelete='cascade')
    
    # Informations personnelles
    name = fields.Char('Nom Complet', required=True)
    relationship = fields.Selection([
        ('father', 'Père'),
        ('mother', 'Mère'),
        ('grandfather', 'Grand-père'),
        ('grandmother', 'Grand-mère'),
        ('uncle', 'Oncle'),
        ('aunt', 'Tante'),
        ('brother', 'Frère'),
        ('sister', 'Sœur'),
        ('guardian', 'Tuteur Légal'),
        ('foster', 'Famille d\'Accueil'),
        ('other', 'Autre')
    ], string='Lien de Parenté', required=True)
    
    # Contact
    phone = fields.Char('Téléphone', required=True)
    email = fields.Char('Email')
    address = fields.Text('Adresse')
    
    # Statut légal
    is_legal_guardian = fields.Boolean('Tuteur Légal')
    has_custody = fields.Boolean('Garde de l\'Enfant')
    can_pick_up = fields.Boolean('Autorisé à Récupérer', default=True)
    emergency_contact = fields.Boolean('Contact d\'Urgence', default=False)
    
    # Priorité
    priority = fields.Selection([
        ('primary', 'Principal'),
        ('secondary', 'Secondaire'),
        ('emergency', 'Urgence Seulement')
    ], string='Priorité', default='secondary')
    
    # Documents
    id_document = fields.Binary('Pièce d\'Identité', attachment=True)
    custody_document = fields.Binary('Document de Garde', attachment=True)
    
    # Préférences de communication
    preferred_contact_time = fields.Selection([
        ('morning', 'Matin (8h-12h)'),
        ('afternoon', 'Après-midi (12h-18h)'),
        ('evening', 'Soir (18h-20h)'),
        ('anytime', 'N\'importe quand')
    ], string='Heure Préférée Contact', default='anytime')
    
    # Métadonnées
    notes = fields.Text('Notes')
    active = fields.Boolean('Actif', default=True)

class FamilyMeetingWizard(models.TransientModel):
    """Assistant pour programmer une réunion familiale"""
    _name = 'family.meeting.wizard'
    _description = 'Assistant Réunion Familiale'
    
    family_id = fields.Many2one('student.family.group', string='Famille', required=True)
    
    # Détails de la réunion
    subject = fields.Char('Sujet', required=True)
    description = fields.Text('Description')
    meeting_type = fields.Selection([
        ('academic', 'Académique'),
        ('behavioral', 'Comportemental'),
        ('administrative', 'Administratif'),
        ('orientation', 'Orientation'),
        ('emergency', 'Urgence')
    ], string='Type de Réunion', required=True)
    
    # Planification
    proposed_date = fields.Datetime('Date Proposée', required=True)
    duration = fields.Float('Durée (heures)', default=1.0)
    location = fields.Selection([
        ('school', 'École'),
        ('home', 'Domicile'),
        ('online', 'En Ligne'),
        ('other', 'Autre Lieu')
    ], string='Lieu', default='school')
    
    # Participants
    include_all_children = fields.Boolean('Inclure Tous les Enfants', default=True)
    specific_children_ids = fields.Many2many('op.student', string='Enfants Spécifiques')
    include_teachers = fields.Boolean('Inclure Enseignants')
    teacher_ids = fields.Many2many('op.faculty', string='Enseignants')
    
    # Priorité
    priority = fields.Selection([
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente')
    ], string='Priorité', default='normal')
    
    notes = fields.Text('Notes Additionnelles')
    
    def action_schedule_meeting(self):
        """Programmer la réunion"""
        # Créer l'événement calendrier
        event = self.env['calendar.event'].create({
            'name': f"Réunion Famille {self.family_id.family_name} - {self.subject}",
            'description': self.description,
            'start': self.proposed_date,
            'stop': self.proposed_date + timedelta(hours=self.duration),
            'location': dict(self._fields['location'].selection)[self.location],
            'allday': False,
        })
        
        # Envoyer les invitations
        # Logique d'invitation à implémenter
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Réunion programmée pour la famille {self.family_id.family_name}',
                'type': 'success'
            }
        }

class FamilyCommunicationWizard(models.TransientModel):
    """Assistant pour communication familiale"""
    _name = 'family.communication.wizard'
    _description = 'Assistant Communication Familiale'
    
    family_id = fields.Many2one('student.family.group', string='Famille', required=True)
    
    # Message
    subject = fields.Char('Sujet', required=True)
    message = fields.Html('Message', required=True)
    message_type = fields.Selection([
        ('info', 'Information'),
        ('reminder', 'Rappel'),
        ('invitation', 'Invitation'),
        ('alert', 'Alerte'),
        ('congratulations', 'Félicitations')
    ], string='Type de Message', default='info')
    
    # Canaux de communication
    send_email = fields.Boolean('Envoyer par Email', default=True)
    send_sms = fields.Boolean('Envoyer par SMS')
    send_whatsapp = fields.Boolean('Envoyer par WhatsApp')
    
    # Destinataires
    include_parents = fields.Boolean('Inclure Parents', default=True)
    include_guardians = fields.Boolean('Inclure Tuteurs', default=True)
    include_emergency_contacts = fields.Boolean('Inclure Contacts d\'Urgence')
    
    # Planification
    send_immediately = fields.Boolean('Envoyer Immédiatement', default=True)
    scheduled_date = fields.Datetime('Programmer pour')
    
    # Options
    request_confirmation = fields.Boolean('Demander Confirmation de Lecture')
    is_urgent = fields.Boolean('Urgent')
    
    def action_send_communication(self):
        """Envoyer la communication"""
        # Logique d'envoi selon les canaux sélectionnés
        # À implémenter avec le module de communication
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Communication envoyée à la famille {self.family_id.family_name}',
                'type': 'success'
            }
        }
