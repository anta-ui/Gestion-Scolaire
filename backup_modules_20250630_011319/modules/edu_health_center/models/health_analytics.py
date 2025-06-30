# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HealthAnalysis(models.Model):
    """Analyses de santé et épidémiologie"""
    _name = 'health.analysis'
    _description = 'Analyse de Santé'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'analysis_date desc'

    name = fields.Char(
        string='Nom de l\'analyse',
        required=True,
        tracking=True
    )
    
    # Type d'analyse
    analysis_type = fields.Selection([
        ('epidemic', 'Analyse épidémiologique'),
        ('vaccination', 'Couverture vaccinale'),
        ('emergency', 'Analyse des urgences'),
        ('medication', 'Consommation médicaments'),
        ('consultation', 'Statistiques consultations'),
        ('insurance', 'Analyse assurances'),
        ('staff', 'Performance personnel'),
        ('general', 'Analyse générale')
    ], string='Type d\'analyse', required=True, default='general')
    
    # Période d'analyse
    analysis_date = fields.Date(
        string='Date d\'analyse',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    period_start = fields.Date(
        string='Début de période',
        required=True
    )
    
    period_end = fields.Date(
        string='Fin de période',
        required=True
    )
    
    # Résultats de l'analyse
    total_students = fields.Integer(
        string='Nombre total d\'étudiants',
        compute='_compute_statistics'
    )
    
    total_consultations = fields.Integer(
        string='Nombre de consultations',
        compute='_compute_statistics'
    )
    
    total_emergencies = fields.Integer(
        string='Nombre d\'urgences',
        compute='_compute_statistics'
    )
    
    total_vaccinations = fields.Integer(
        string='Nombre de vaccinations',
        compute='_compute_statistics'
    )
    
    # Indicateurs de risque
    risk_level = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique')
    ], string='Niveau de risque', compute='_compute_risk_level', store=True)
    
    epidemic_risk = fields.Boolean(
        string='Risque épidémique',
        compute='_compute_epidemic_risk'
    )
    
    # Recommandations
    recommendations = fields.Text(
        string='Recommandations',
        help="Recommandations basées sur l'analyse"
    )
    
    ai_recommendations = fields.Text(
        string='Recommandations IA',
        compute='_compute_ai_recommendations',
        help="Recommandations générées par IA"
    )
    
    # Alertes
    alert_ids = fields.One2many(
        'health.alert',
        'analysis_id',
        string='Alertes'
    )
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('archived', 'Archivée')
    ], string='État', default='draft', tracking=True)
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    @api.depends('period_start', 'period_end')
    def _compute_statistics(self):
        """Calculer les statistiques de base"""
        for analysis in self:
            if analysis.period_start and analysis.period_end:
                # Nombre total d'étudiants
                students = self.env['op.student'].search([])
                analysis.total_students = len(students)
                
                # Consultations dans la période
                consultations = self.env['edu.medical.consultation'].search([
                    ('consultation_date', '>=', analysis.period_start),
                    ('consultation_date', '<=', analysis.period_end)
                ])
                analysis.total_consultations = len(consultations)
                
                # Urgences dans la période
                emergencies = self.env['health.emergency'].search([
                    ('emergency_date', '>=', analysis.period_start),
                    ('emergency_date', '<=', analysis.period_end)
                ])
                analysis.total_emergencies = len(emergencies)
                
                # Vaccinations dans la période
                vaccinations = self.env['vaccination.record'].search([
                    ('vaccination_date', '>=', analysis.period_start),
                    ('vaccination_date', '<=', analysis.period_end)
                ])
                analysis.total_vaccinations = len(vaccinations)
            else:
                analysis.total_students = 0
                analysis.total_consultations = 0
                analysis.total_emergencies = 0
                analysis.total_vaccinations = 0
    
    @api.depends('total_emergencies', 'total_consultations', 'epidemic_risk')
    def _compute_risk_level(self):
        """Calculer le niveau de risque"""
        for analysis in self:
            if analysis.epidemic_risk:
                analysis.risk_level = 'critical'
            elif analysis.total_emergencies > 10:
                analysis.risk_level = 'high'
            elif analysis.total_emergencies > 5:
                analysis.risk_level = 'medium'
            else:
                analysis.risk_level = 'low'
    
    def _compute_epidemic_risk(self):
        """Détecter les risques épidémiques"""
        for analysis in self:
            # Logique simple de détection d'épidémie
            # Plus de 5 urgences ou consultations par jour en moyenne
            if analysis.period_start and analysis.period_end:
                days = (analysis.period_end - analysis.period_start).days + 1
                daily_avg = (analysis.total_emergencies + analysis.total_consultations) / days
                analysis.epidemic_risk = daily_avg > 5
            else:
                analysis.epidemic_risk = False
    
    def _compute_ai_recommendations(self):
        """Générer des recommandations IA"""
        for analysis in self:
            recommendations = []
            
            if analysis.epidemic_risk:
                recommendations.append("🚨 Risque épidémique détecté - Renforcer les mesures de prévention")
            
            if analysis.total_emergencies > 10:
                recommendations.append("⚠️ Nombre élevé d'urgences - Vérifier les protocoles de sécurité")
            
            if analysis.total_vaccinations < analysis.total_students * 0.8:
                recommendations.append("💉 Couverture vaccinale insuffisante - Organiser une campagne de vaccination")
            
            if analysis.total_consultations < analysis.total_students * 0.1:
                recommendations.append("🏥 Faible taux de consultation - Sensibiliser à l'importance du suivi médical")
            
            analysis.ai_recommendations = '\n'.join(recommendations) if recommendations else "Aucune recommandation particulière"
    
    def action_start_analysis(self):
        """Démarrer l'analyse"""
        self.state = 'in_progress'
        self._generate_alerts()
    
    def action_complete_analysis(self):
        """Terminer l'analyse"""
        self.state = 'completed'
    
    def _generate_alerts(self):
        """Générer des alertes basées sur l'analyse"""
        self.ensure_one()
        
        # Supprimer les anciennes alertes
        self.alert_ids.unlink()
        
        alerts = []
        
        if self.epidemic_risk:
            alerts.append({
                'name': 'Alerte épidémique',
                'alert_type': 'epidemic',
                'severity': 'critical',
                'message': 'Risque épidémique détecté dans l\'établissement',
                'analysis_id': self.id
            })
        
        if self.total_emergencies > 10:
            alerts.append({
                'name': 'Nombre élevé d\'urgences',
                'alert_type': 'emergency',
                'severity': 'high',
                'message': f'{self.total_emergencies} urgences enregistrées dans la période',
                'analysis_id': self.id
            })
        
        # Créer les alertes
        for alert_data in alerts:
            self.env['health.alert'].create(alert_data)


class HealthAlert(models.Model):
    """Alertes de santé"""
    _name = 'health.alert'
    _description = 'Alerte de Santé'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Nom de l\'alerte',
        required=True,
        tracking=True
    )
    
    alert_type = fields.Selection([
        ('epidemic', 'Épidémie'),
        ('emergency', 'Urgence'),
        ('vaccination', 'Vaccination'),
        ('medication', 'Médicament'),
        ('staff', 'Personnel'),
        ('equipment', 'Équipement'),
        ('other', 'Autre')
    ], string='Type d\'alerte', required=True)
    
    severity = fields.Selection([
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('high', 'Élevé'),
        ('critical', 'Critique')
    ], string='Sévérité', required=True, default='info')
    
    message = fields.Text(
        string='Message',
        required=True,
        help="Description détaillée de l'alerte"
    )
    
    # Relations
    analysis_id = fields.Many2one(
        'health.analysis',
        string='Analyse liée'
    )
    
    # État
    state = fields.Selection([
        ('active', 'Active'),
        ('acknowledged', 'Accusée réception'),
        ('resolved', 'Résolue'),
        ('dismissed', 'Ignorée')
    ], string='État', default='active', tracking=True)
    
    # Dates
    alert_date = fields.Datetime(
        string='Date d\'alerte',
        default=fields.Datetime.now,
        required=True
    )
    
    acknowledged_date = fields.Datetime(
        string='Date accusé réception'
    )
    
    resolved_date = fields.Datetime(
        string='Date de résolution'
    )
    
    # Responsable
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        help="Utilisateur responsable de traiter l'alerte"
    )
    
    # Actions prises
    actions_taken = fields.Text(
        string='Actions prises',
        help="Description des actions prises pour résoudre l'alerte"
    )
    
    def action_acknowledge(self):
        """Accuser réception de l'alerte"""
        self.write({
            'state': 'acknowledged',
            'acknowledged_date': fields.Datetime.now(),
            'responsible_id': self.env.user.id
        })
    
    def action_resolve(self):
        """Marquer l'alerte comme résolue"""
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now()
        })
    
    def action_dismiss(self):
        """Ignorer l'alerte"""
        self.state = 'dismissed'


class HealthDashboard(models.Model):
    """Tableau de bord santé"""
    _name = 'health.dashboard'
    _description = 'Tableau de Bord Santé'
    _order = 'name'

    name = fields.Char(
        string='Nom du tableau de bord',
        required=True
    )
    
    # Indicateurs temps réel
    active_emergencies = fields.Integer(
        string='Urgences actives',
        compute='_compute_realtime_stats'
    )
    
    consultations_today = fields.Integer(
        string='Consultations aujourd\'hui',
        compute='_compute_realtime_stats'
    )
    
    vaccinations_due = fields.Integer(
        string='Vaccinations dues',
        compute='_compute_realtime_stats'
    )
    
    low_stock_medications = fields.Integer(
        string='Médicaments en stock faible',
        compute='_compute_realtime_stats'
    )
    
    staff_on_duty = fields.Integer(
        string='Personnel de garde',
        compute='_compute_realtime_stats'
    )
    
    active_alerts = fields.Integer(
        string='Alertes actives',
        compute='_compute_realtime_stats'
    )
    
    # Tendances
    consultation_trend = fields.Selection([
        ('up', 'En hausse'),
        ('stable', 'Stable'),
        ('down', 'En baisse')
    ], string='Tendance consultations', compute='_compute_trends')
    
    emergency_trend = fields.Selection([
        ('up', 'En hausse'),
        ('stable', 'Stable'),
        ('down', 'En baisse')
    ], string='Tendance urgences', compute='_compute_trends')
    
    # Dernière mise à jour
    last_update = fields.Datetime(
        string='Dernière mise à jour',
        default=fields.Datetime.now
    )
    
    def _compute_realtime_stats(self):
        """Calculer les statistiques temps réel"""
        for dashboard in self:
            today = fields.Date.today()
            
            # Urgences actives
            dashboard.active_emergencies = self.env['health.emergency'].search_count([
                ('state', '=', 'active')
            ])
            
            # Consultations aujourd'hui
            dashboard.consultations_today = self.env['edu.medical.consultation'].search_count([
                ('consultation_date', '=', today)
            ])
            
            # Vaccinations dues
            dashboard.vaccinations_due = self.env['vaccination.record'].search_count([
                ('next_vaccination_date', '<=', today),
                ('state', '=', 'scheduled')
            ])
            
            # Médicaments en stock faible
            dashboard.low_stock_medications = self.env['medication.stock'].search_count([
                ('current_stock', '<=', 'minimum_stock')
            ])
            
            # Personnel de garde
            dashboard.staff_on_duty = self.env['medical.staff'].search_count([
                ('is_on_duty', '=', True)
            ])
            
            # Alertes actives
            dashboard.active_alerts = self.env['health.alert'].search_count([
                ('state', '=', 'active')
            ])
    
    def _compute_trends(self):
        """Calculer les tendances"""
        for dashboard in self:
            # Logique simplifiée pour les tendances
            # Comparaison avec la semaine précédente
            today = fields.Date.today()
            week_ago = today - timedelta(days=7)
            two_weeks_ago = today - timedelta(days=14)
            
            # Consultations cette semaine vs semaine dernière
            consultations_this_week = self.env['edu.medical.consultation'].search_count([
                ('consultation_date', '>=', week_ago),
                ('consultation_date', '<=', today)
            ])
            
            consultations_last_week = self.env['edu.medical.consultation'].search_count([
                ('consultation_date', '>=', two_weeks_ago),
                ('consultation_date', '<', week_ago)
            ])
            
            if consultations_this_week > consultations_last_week * 1.1:
                dashboard.consultation_trend = 'up'
            elif consultations_this_week < consultations_last_week * 0.9:
                dashboard.consultation_trend = 'down'
            else:
                dashboard.consultation_trend = 'stable'
            
            # Urgences cette semaine vs semaine dernière
            emergencies_this_week = self.env['health.emergency'].search_count([
                ('emergency_date', '>=', week_ago),
                ('emergency_date', '<=', today)
            ])
            
            emergencies_last_week = self.env['health.emergency'].search_count([
                ('emergency_date', '>=', two_weeks_ago),
                ('emergency_date', '<', week_ago)
            ])
            
            if emergencies_this_week > emergencies_last_week * 1.1:
                dashboard.emergency_trend = 'up'
            elif emergencies_this_week < emergencies_last_week * 0.9:
                dashboard.emergency_trend = 'down'
            else:
                dashboard.emergency_trend = 'stable'
    
    def action_refresh(self):
        """Actualiser le tableau de bord"""
        self.last_update = fields.Datetime.now()
        # Force le recalcul des champs computed
        self._compute_realtime_stats()
        self._compute_trends()
