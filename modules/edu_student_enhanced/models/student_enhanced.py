# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import uuid
import json
import qrcode
import io
import base64

class StudentEnhanced(models.Model):
    """Modèle élève extraordinaire avec toutes les fonctionnalités modernes"""
    _inherit = 'op.student'
    _description = 'Élève Extraordinaire'

    # ===============================
    # CHAMPS IDENTITÉ ÉTENDUE
    # ===============================
    
    # QR Code unique pour chaque élève
    qr_code = fields.Text('QR Code', compute='_compute_qr_code', store=True)
    qr_code_image = fields.Binary('QR Code Image', compute='_compute_qr_code_image', store=True)
    unique_code = fields.Char('Code Unique', default=lambda self: str(uuid.uuid4())[:8].upper())
    
    # Photos et documents
    profile_picture = fields.Binary('Photo de Profil', attachment=True)
    id_card_front = fields.Binary('Carte d\'Identité Recto', attachment=True)
    id_card_back = fields.Binary('Carte d\'Identité Verso', attachment=True)
    birth_certificate = fields.Binary('Acte de Naissance', attachment=True)
    
    # Informations personnelles étendues
    nationality_text = fields.Char('Nationalité Texte', default='Sénégalaise')
    religion_choice = fields.Selection([
        ('islam', 'Islam'),
        ('christianisme', 'Christianisme'),
        ('autres', 'Autres'),
        ('non_renseigne', 'Non renseigné')
    ], string='Religion', default='non_renseigne')
    languages_spoken = fields.Char('Langues Parlées', default='Français, Wolof')
    special_needs = fields.Text('Besoins Spéciaux')
    
    # Géolocalisation
    home_address_gps = fields.Char('Coordonnées GPS Domicile')
    pickup_point = fields.Char('Point de Ramassage')
    
    # ===============================
    # RELATIONS FAMILIALES
    # ===============================
    
    family_group_id = fields.Many2one('student.family.group', string='Groupe Familial')
    siblings_count = fields.Integer('Nombre de Frères/Sœurs', compute='_compute_siblings_count')
    siblings_ids = fields.Many2many('op.student', 'student_sibling_rel', 'student_id', 'sibling_id', string='Frères et Sœurs')
    
    guardian_type = fields.Selection([
        ('both_parents', 'Deux Parents'),
        ('single_parent', 'Parent Unique'),
        ('guardian', 'Tuteur'),
        ('other', 'Autre')
    ], string='Type de Garde', default='both_parents')
    
    # ===============================
    # INFORMATIONS MÉDICALES
    # ===============================
    
    medical_info_ids = fields.One2many('student.medical.info', 'student_id', string='Informations Médicales')
    allergies = fields.Text('Allergies')
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-')
    ], string='Groupe Sanguin', default='O+')
    chronic_diseases = fields.Text('Maladies Chroniques')
    current_medications = fields.Text('Médicaments Actuels')
    doctor_name = fields.Char('Nom du Médecin Traitant')
    doctor_phone = fields.Char('Téléphone Médecin')
    
    # Alertes médicales
    has_medical_alerts = fields.Boolean('Alertes Médicales', compute='_compute_medical_alerts')
    medical_alerts_count = fields.Integer('Nombre d\'Alertes', compute='_compute_medical_alerts')
    
    # ===============================
    # SUIVI COMPORTEMENTAL
    # ===============================
    
    behavior_records_ids = fields.One2many('student.behavior.record', 'student_id', string='Historique Comportemental')
    behavior_score = fields.Float('Score Comportemental', compute='_compute_behavior_score', store=True)
    behavior_trend = fields.Selection([
        ('improving', '📈 En Amélioration'),
        ('stable', '📊 Stable'),
        ('declining', '📉 En Dégradation')
    ], string='Tendance Comportementale', compute='_compute_behavior_trend')
    
    rewards_count = fields.Integer('Nombre de Récompenses', compute='_compute_behavior_stats')
    sanctions_count = fields.Integer('Nombre de Sanctions', compute='_compute_behavior_stats')
    
    # ===============================
    # GESTION DOCUMENTS
    # ===============================
    
    documents_ids = fields.One2many('student.document', 'student_id', string='Documents')
    documents_complete = fields.Boolean('Dossier Complet', compute='_compute_documents_status')
    missing_documents = fields.Text('Documents Manquants', compute='_compute_documents_status')
    
    # ===============================
    # ANALYTICS ET IA
    # ===============================
    
    risk_dropout = fields.Float('Risque de Décrochage (%)', compute='_compute_dropout_risk')
    performance_prediction = fields.Selection([
        ('excellent', '🌟 Excellence'),
        ('good', '👍 Bon'),
        ('average', '📊 Moyen'),
        ('at_risk', '⚠️ À Risque')
    ], string='Prédiction Performance', compute='_compute_performance_prediction')
    
    last_activity_date = fields.Datetime('Dernière Activité', default=fields.Datetime.now)
    engagement_score = fields.Float('Score d\'Engagement', compute='_compute_engagement_score')
    
    # ===============================
    # TRANSPORT ET LOCALISATION
    # ===============================
    
    transport_required = fields.Boolean('Transport Requis')
    bus_route = fields.Char('Ligne de Bus')
    pickup_time = fields.Float('Heure de Ramassage')
    dropoff_time = fields.Float('Heure de Dépose')
    
    # ===============================
    # MÉTHODES COMPUTE
    # ===============================
    
    @api.depends('unique_code', 'name')
    def _compute_qr_code(self):
        """Générer le QR code unique pour l'élève"""
        for student in self:
            qr_data = {
                'student_id': student.id if isinstance(student.id, int) else student.id.ref,
                'unique_code': student.unique_code,
                'name': student.name,
            }
            student.qr_code = json.dumps(qr_data)
    
    @api.depends('qr_code')
    def _compute_qr_code_image(self):
        """Générer l'image QR Code"""
        for student in self:
            if student.qr_code:
                try:
                    # Créer le QR code
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(student.qr_code)
                    qr.make(fit=True)
                    
                    # Créer l'image
                    img = qr.make_image(fill_color="black", back_color="white")
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    
                    # Encoder en base64
                    student.qr_code_image = base64.b64encode(buffer.getvalue())
                except:
                    student.qr_code_image = False
            else:
                student.qr_code_image = False
    
    @api.depends('siblings_ids')
    def _compute_siblings_count(self):
        """Calculer le nombre de frères et sœurs"""
        for student in self:
            if student.siblings_ids:
                student.siblings_count = len(student.siblings_ids)
            else:
                student.siblings_count = 0
    
    @api.depends('medical_info_ids', 'allergies', 'chronic_diseases')
    def _compute_medical_alerts(self):
        """Calculer les alertes médicales"""
        for student in self:
            alerts = 0
            if student.allergies:
                alerts += 1
            if student.chronic_diseases:
                alerts += 1
            student.medical_alerts_count = alerts
            student.has_medical_alerts = alerts > 0
    
    @api.depends('behavior_records_ids.points')
    def _compute_behavior_score(self):
        """Calculer le score comportemental"""
        for student in self:
            if student.behavior_records_ids:
                total_points = sum(student.behavior_records_ids.mapped('points'))
                student.behavior_score = total_points
            else:
                student.behavior_score = 0
    
    def _compute_behavior_trend(self):
        """Analyser la tendance comportementale"""
        for student in self:
            student.behavior_trend = 'stable'  # Valeur par défaut
    
    @api.depends('behavior_records_ids.type')
    def _compute_behavior_stats(self):
        """Calculer les statistiques comportementales"""
        for student in self:
            if student.behavior_records_ids:
                records = student.behavior_records_ids
                student.rewards_count = len(records.filtered(lambda r: r.type == 'reward'))
                student.sanctions_count = len(records.filtered(lambda r: r.type == 'sanction'))
            else:
                student.rewards_count = 0
                student.sanctions_count = 0
    
    def _compute_documents_status(self):
        """Calculer le statut des documents"""
        for student in self:
            # Pour l'instant, on considère le dossier comme incomplet
            student.documents_complete = False
            student.missing_documents = "Fonctionnalité en cours de développement"
    
    def _compute_dropout_risk(self):
        """IA: Calculer le risque de décrochage"""
        for student in self:
            risk_factors = 0
            
            if student.behavior_score < -10:
                risk_factors += 30
            
            if student.special_needs:
                risk_factors += 20
            
            if student.engagement_score < 50:
                risk_factors += 25
            
            student.risk_dropout = min(risk_factors, 100)
    
    def _compute_performance_prediction(self):
        """IA: Prédire la performance future"""
        for student in self:
            score = 50  # Score de base
            
            if student.behavior_trend == 'improving':
                score += 20
            elif student.behavior_trend == 'declining':
                score -= 20
            
            score += min(student.behavior_score * 2, 30)
            score += student.engagement_score * 0.2
            score += (100 - student.risk_dropout) * 0.2
            
            if score >= 80:
                student.performance_prediction = 'excellent'
            elif score >= 60:
                student.performance_prediction = 'good'
            elif score >= 40:
                student.performance_prediction = 'average'
            else:
                student.performance_prediction = 'at_risk'
    
    def _compute_engagement_score(self):
        """Calculer le score d'engagement"""
        for student in self:
            score = 50  # Score de base
            
            if student.rewards_count > student.sanctions_count:
                score += 15
            elif student.sanctions_count > student.rewards_count:
                score -= 10
            
            student.engagement_score = max(0, min(score, 100))
    
    # ===============================
    # MÉTHODES D'ACTION
    # ===============================
    
    def action_generate_student_card(self):
        """Génère une carte d'élève"""
        self.ensure_one()
        return self.env.ref('edu_student_enhanced.student_card_report').report_action(self)
    
    def action_view_medical_file(self):
        """Affiche le dossier médical de l'élève"""
        self.ensure_one()
        return {
            'name': _('Dossier Médical'),
            'type': 'ir.actions.act_window',
            'res_model': 'student.medical.info',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_behavior_history(self):
        """Affiche l'historique comportemental de l'élève"""
        self.ensure_one()
        return {
            'name': _('Historique Comportemental'),
            'type': 'ir.actions.act_window',
            'res_model': 'student.behavior.record',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_send_parent_alert(self):
        """Ouvre l'assistant d'alerte parents"""
        self.ensure_one()
        return {
            'name': _('Envoyer une Alerte'),
            'type': 'ir.actions.act_window',
            'res_model': 'parent.alert.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_student_id': self.id},
        }
    
    def update_last_activity(self):
        """Mettre à jour la dernière activité"""
        self.last_activity_date = fields.Datetime.now()
    
    @api.model
    def create(self, vals):
        """Surcharge create pour générer le code unique"""
        if not vals.get('unique_code'):
            vals['unique_code'] = str(uuid.uuid4())[:8].upper()
        return super().create(vals)

class StudentCategory(models.Model):
    """Catégories d'élèves pour classification"""
    _name = 'student.category'
    _description = 'Catégorie d\'Élève'
    _order = 'sequence, name'
    
    name = fields.Char('Nom', required=True, translate=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')
    color = fields.Integer('Couleur', default=1)
    criteria = fields.Text('Critères d\'Attribution')
    benefits = fields.Text('Avantages/Bénéfices')
    sequence = fields.Integer('Séquence', default=10)
    active = fields.Boolean('Actif', default=True)
    icon = fields.Char('Icône')
    
    # Statistiques
    student_count = fields.Integer('Nombre d\'Élèves', compute='_compute_student_count')
    
    @api.depends()
    def _compute_student_count(self):
        """Calculer le nombre d'élèves dans cette catégorie"""
        for category in self:
            category.student_count = 0  # Fonctionnalité à implémenter
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Le code de la catégorie doit être unique.'),
    ]

