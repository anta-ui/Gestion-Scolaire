# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HealthAnalytics(models.Model):
    """Modèle pour les analyses de santé"""
    _name = 'health.analytics'
    _description = 'Analyse de Santé'
    _order = 'create_date desc'
    
    name = fields.Char(
        string='Nom de l\'analyse',
        required=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    analysis_type = fields.Selection([
        ('general', 'Analyse générale'),
        ('vaccination', 'Couverture vaccinale'),
        ('epidemic', 'Surveillance épidémiologique'),
        ('nutrition', 'Analyse nutritionnelle'),
        ('mental_health', 'Santé mentale'),
        ('chronic_disease', 'Maladies chroniques'),
        ('emergency', 'Urgences'),
        ('consultation', 'Consultations'),
        ('custom', 'Personnalisée')
    ], string='Type d\'analyse', default='general', required=True)
    
    period_start = fields.Date(
        string='Début de période',
        required=True,
        default=lambda self: fields.Date.today() - timedelta(days=30)
    )
    
    period_end = fields.Date(
        string='Fin de période',
        required=True,
        default=fields.Date.today
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', required=True)
    
    # Résultats de l'analyse
    total_students = fields.Integer(
        string='Total étudiants',
        compute='_compute_statistics',
        store=True
    )
    
    total_consultations = fields.Integer(
        string='Total consultations',
        compute='_compute_statistics',
        store=True
    )
    
    total_vaccinations = fields.Integer(
        string='Total vaccinations',
        compute='_compute_statistics',
        store=True
    )
    
    total_emergencies = fields.Integer(
        string='Total urgences',
        compute='_compute_statistics',
        store=True
    )
    
    # Taux et pourcentages
    vaccination_rate = fields.Float(
        string='Taux de vaccination (%)',
        compute='_compute_rates',
        store=True
    )
    
    emergency_rate = fields.Float(
        string='Taux d\'urgence (%)',
        compute='_compute_rates',
        store=True
    )
    
    consultation_rate = fields.Float(
        string='Taux de consultation (%)',
        compute='_compute_rates',
        store=True
    )
    
    # Données JSON pour les graphiques
    chart_data = fields.Text(
        string='Données graphiques',
        help='Données JSON pour les graphiques'
    )
    
    # Rapports
    analysis_report = fields.Html(
        string='Rapport d\'analyse',
        compute='_compute_analysis_report'
    )
    
    recommendations = fields.Html(
        string='Recommandations',
        compute='_compute_recommendations'
    )
    
    key_findings = fields.Html(
        string='Principales découvertes',
        compute='_compute_key_findings'
    )
    
    # Métadonnées
    created_by = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        required=True
    )
    
    generation_date = fields.Datetime(
        string='Date de génération',
        default=fields.Datetime.now
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    # Champs pour les statistiques détaillées
    consultations_count = fields.Integer(
        string='Nombre de consultations',
        compute='_compute_detailed_stats'
    )
    
    emergencies_count = fields.Integer(
        string='Nombre d\'urgences',
        compute='_compute_detailed_stats'
    )
    
    @api.depends('period_start', 'period_end', 'analysis_type')
    def _compute_statistics(self):
        """Calculer les statistiques de base"""
        for record in self:
            # Compter les étudiants actifs
            health_records = self.env['edu.health.record'].search([
                ('active', '=', True)
            ])
            record.total_students = len(health_records)
            
            # Compter les consultations dans la période
            consultations = self.env['edu.medical.consultation'].search([
                ('consultation_date', '>=', record.period_start),
                ('consultation_date', '<=', record.period_end),
                ('state', '=', 'completed')
            ])
            record.total_consultations = len(consultations)
            
            # Compter les vaccinations dans la période
            vaccinations = self.env['vaccination.record'].search([
                ('vaccination_date', '>=', record.period_start),
                ('vaccination_date', '<=', record.period_end)
            ])
            record.total_vaccinations = len(vaccinations)
            
            # Compter les urgences dans la période
            emergencies = self.env['health.emergency'].search([
                ('emergency_date', '>=', record.period_start),
                ('emergency_date', '<=', record.period_end)
            ])
            record.total_emergencies = len(emergencies)
    
    @api.depends('total_students', 'total_vaccinations', 'total_emergencies', 'total_consultations')
    def _compute_rates(self):
        """Calculer les taux"""
        for record in self:
            if record.total_students > 0:
                record.vaccination_rate = (record.total_vaccinations / record.total_students) * 100
                record.emergency_rate = (record.total_emergencies / record.total_students) * 100
                record.consultation_rate = (record.total_consultations / record.total_students) * 100
            else:
                record.vaccination_rate = 0.0
                record.emergency_rate = 0.0
                record.consultation_rate = 0.0
    
    @api.depends('analysis_type', 'total_students', 'total_consultations', 'vaccination_rate', 'emergency_rate')
    def _compute_analysis_report(self):
        """Générer le rapport d'analyse"""
        for record in self:
            if record.analysis_type == 'general':
                record.analysis_report = f"""
                <div class="container">
                    <h3>📊 Rapport d'Analyse Générale</h3>
                    <div class="row">
                        <div class="col-md-6">
                            <h4>Période d'analyse</h4>
                            <p><strong>Du:</strong> {record.period_start}</p>
                            <p><strong>Au:</strong> {record.period_end}</p>
                        </div>
                        <div class="col-md-6">
                            <h4>Statistiques principales</h4>
                            <ul>
                                <li><strong>Total d'étudiants:</strong> {record.total_students}</li>
                                <li><strong>Consultations:</strong> {record.total_consultations}</li>
                                <li><strong>Vaccinations:</strong> {record.total_vaccinations}</li>
                                <li><strong>Urgences:</strong> {record.total_emergencies}</li>
                            </ul>
                        </div>
                    </div>
                    <div class="row mt-3">
                        <div class="col-md-12">
                            <h4>Indicateurs de performance</h4>
                            <div class="progress-container">
                                <p><strong>Taux de vaccination:</strong> {record.vaccination_rate:.1f}%</p>
                                <p><strong>Taux de consultation:</strong> {record.consultation_rate:.1f}%</p>
                                <p><strong>Taux d'urgence:</strong> {record.emergency_rate:.1f}%</p>
                            </div>
                        </div>
                    </div>
                </div>
                """
            elif record.analysis_type == 'vaccination':
                record.analysis_report = f"""
                <h3>💉 Analyse de la Couverture Vaccinale</h3>
                <p><strong>Période:</strong> {record.period_start} - {record.period_end}</p>
                <p><strong>Vaccinations effectuées:</strong> {record.total_vaccinations}</p>
                <p><strong>Taux de couverture:</strong> {record.vaccination_rate:.1f}%</p>
                """
            elif record.analysis_type == 'emergency':
                record.analysis_report = f"""
                <h3>🚨 Analyse des Urgences</h3>
                <p><strong>Période:</strong> {record.period_start} - {record.period_end}</p>
                <p><strong>Urgences traitées:</strong> {record.total_emergencies}</p>
                <p><strong>Taux d'urgence:</strong> {record.emergency_rate:.1f}%</p>
                """
            else:
                record.analysis_report = f"""
                <h3>📋 Analyse {record.analysis_type.replace('_', ' ').title()}</h3>
                <p>Analyse en cours de développement pour ce type.</p>
                <p><strong>Période:</strong> {record.period_start} - {record.period_end}</p>
                """
    
    @api.depends('analysis_type', 'vaccination_rate', 'emergency_rate', 'consultation_rate')
    def _compute_recommendations(self):
        """Générer les recommandations"""
        for record in self:
            recommendations = []
            
            # Recommandations basées sur les taux
            if record.vaccination_rate < 80:
                recommendations.append("⚠️ Le taux de vaccination est inférieur à 80%. Envisager une campagne de sensibilisation.")
            
            if record.emergency_rate > 10:
                recommendations.append("🚨 Le taux d'urgence est élevé. Réviser les protocoles de prévention.")
            
            if record.consultation_rate < 20:
                recommendations.append("👩‍⚕️ Le taux de consultation est faible. Encourager les consultations préventives.")
            
            if record.vaccination_rate >= 90:
                recommendations.append("✅ Excellent taux de vaccination. Maintenir les efforts.")
            
            if not recommendations:
                recommendations.append("📊 Les indicateurs sont dans les normes acceptables.")
            
            record.recommendations = "<ul>" + "".join([f"<li>{rec}</li>" for rec in recommendations]) + "</ul>"
    
    @api.depends('analysis_type', 'total_students', 'total_consultations')
    def _compute_key_findings(self):
        """Calculer les principales découvertes"""
        for record in self:
            findings = []
            
            if record.total_students > 0:
                avg_consultations = record.total_consultations / record.total_students
                if avg_consultations > 2:
                    findings.append(f"📈 Moyenne élevée de consultations par étudiant: {avg_consultations:.1f}")
                elif avg_consultations < 0.5:
                    findings.append(f"📉 Faible moyenne de consultations par étudiant: {avg_consultations:.1f}")
            
            if record.emergency_rate > 5:
                findings.append(f"⚠️ Taux d'urgence préoccupant: {record.emergency_rate:.1f}%")
            
            if record.vaccination_rate > 95:
                findings.append(f"🏆 Excellente couverture vaccinale: {record.vaccination_rate:.1f}%")
            
            if not findings:
                findings.append("📊 Aucune donnée significative identifiée pour cette période.")
            
            record.key_findings = "<ul>" + "".join([f"<li>{finding}</li>" for finding in findings]) + "</ul>"
    
    @api.depends('period_start', 'period_end')
    def _compute_detailed_stats(self):
        """Calculer les statistiques détaillées"""
        for record in self:
            record.consultations_count = record.total_consultations
            record.emergencies_count = record.total_emergencies
    
    def action_generate_analysis(self):
        """Générer l'analyse"""
        self.state = 'in_progress'
        # Forcer le recalcul des champs computed
        self._compute_statistics()
        self._compute_rates()
        self._compute_analysis_report()
        self._compute_recommendations()
        self._compute_key_findings()
        self.state = 'completed'
        self.generation_date = fields.Datetime.now()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_export_report(self):
        """Exporter le rapport"""
        return {
            'type': 'ir.actions.report',
            'report_name': 'edu_health_center.health_analytics_report',
            'report_type': 'qweb-pdf',
            'data': {'ids': self.ids},
        }
    
    @api.model
    def create(self, vals):
        """Création avec génération automatique du nom"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            sequence = self.env['ir.sequence'].next_by_code('health.analytics') or _('ANAL-001')
            vals['name'] = f"Analyse {vals.get('analysis_type', 'générale')} - {sequence}"
        return super().create(vals)
