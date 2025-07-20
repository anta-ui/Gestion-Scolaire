# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
import json

class HealthDashboard(models.Model):
    _name = 'health.dashboard'
    _description = 'Tableau de Bord Centre de Santé'
    _order = 'dashboard_date desc'

    name = fields.Char(string='Nom du Tableau de Bord', required=True, default='Tableau de Bord Santé')
    dashboard_date = fields.Date(string='Date', default=fields.Date.today, required=True)
    
    # Indicateurs principaux
    total_students = fields.Integer(string='Total Étudiants', compute='_compute_stats')
    active_cases = fields.Integer(string='Cas Actifs', compute='_compute_stats')
    vaccinations_today = fields.Integer(string='Vaccinations Aujourd\'hui', compute='_compute_stats')
    staff_on_duty = fields.Integer(string='Personnel de Service', compute='_compute_stats')
    consultations_today = fields.Integer(string='Consultations Aujourd\'hui', compute='_compute_stats')
    emergencies_today = fields.Integer(string='Urgences Aujourd\'hui', compute='_compute_stats')
    medications_dispensed = fields.Integer(string='Médicaments Distribués', compute='_compute_stats')
    
    # Tendances
    weekly_trend = fields.Float(string='Tendance Hebdomadaire (%)', compute='_compute_trends')
    monthly_trend = fields.Float(string='Tendance Mensuelle (%)', compute='_compute_trends')
    alert_level = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Modéré'),
        ('high', 'Élevé'),
        ('critical', 'Critique')
    ], string='Niveau d\'Alerte', default='low', compute='_compute_alert_level')
    
    # Graphiques
    chart_consultations = fields.Html(string='Graphique Consultations', compute='_compute_charts')
    chart_top_diseases = fields.Html(string='Top Pathologies', compute='_compute_charts')
    chart_vaccination_rate = fields.Html(string='Taux Vaccination', compute='_compute_charts')
    chart_infirmary_occupancy = fields.Html(string='Occupation Infirmerie', compute='_compute_charts')
    
    # Alertes et recommandations
    active_alerts = fields.Html(string='Alertes Actives', compute='_compute_alerts')
    ai_recommendations = fields.Html(string='Recommandations IA', compute='_compute_recommendations')

    @api.depends('dashboard_date')
    def _compute_stats(self):
        for record in self:
            # Simuler des données (à remplacer par de vraies requêtes)
            record.total_students = 1250
            record.active_cases = 15
            record.vaccinations_today = 8
            record.staff_on_duty = 4
            record.consultations_today = 12
            record.emergencies_today = 2
            record.medications_dispensed = 35

    @api.depends('dashboard_date')
    def _compute_trends(self):
        for record in self:
            # Simuler des tendances
            record.weekly_trend = 5.2
            record.monthly_trend = -2.1

    @api.depends('active_cases', 'emergencies_today')
    def _compute_alert_level(self):
        for record in self:
            if record.emergencies_today >= 5 or record.active_cases >= 30:
                record.alert_level = 'critical'
            elif record.emergencies_today >= 3 or record.active_cases >= 20:
                record.alert_level = 'high'
            elif record.emergencies_today >= 1 or record.active_cases >= 10:
                record.alert_level = 'medium'
            else:
                record.alert_level = 'low'

    @api.depends('dashboard_date')
    def _compute_charts(self):
        for record in self:
            # Graphiques simplifiés en HTML
            record.chart_consultations = '''
                <div class="chart-container">
                    <canvas id="consultationsChart" width="400" height="200"></canvas>
                    <p>Consultations des 7 derniers jours</p>
                </div>
            '''
            record.chart_top_diseases = '''
                <div class="chart-container">
                    <ul>
                        <li>Maux de tête: 25%</li>
                        <li>Rhume: 20%</li>
                        <li>Fatigue: 15%</li>
                        <li>Allergies: 12%</li>
                        <li>Autres: 28%</li>
                    </ul>
                </div>
            '''
            record.chart_vaccination_rate = '''
                <div class="chart-container">
                    <div class="progress">
                        <div class="progress-bar" style="width: 85%">85% vaccinés</div>
                    </div>
                </div>
            '''
            record.chart_infirmary_occupancy = '''
                <div class="chart-container">
                    <p>Occupation actuelle: 3/8 lits</p>
                    <div class="progress">
                        <div class="progress-bar bg-info" style="width: 37.5%">37.5%</div>
                    </div>
                </div>
            '''

    @api.depends('alert_level', 'active_cases')
    def _compute_alerts(self):
        for record in self:
            alerts = []
            if record.alert_level in ['high', 'critical']:
                alerts.append(f'🚨 Niveau d\'alerte: {dict(record._fields["alert_level"].selection)[record.alert_level]}')
            if record.active_cases > 15:
                alerts.append(f'⚠️ {record.active_cases} cas actifs - surveillance recommandée')
            
            if alerts:
                record.active_alerts = '<br/>'.join(alerts)
            else:
                record.active_alerts = '✅ Aucune alerte active'

    @api.depends('weekly_trend', 'monthly_trend')
    def _compute_recommendations(self):
        for record in self:
            recommendations = []
            if record.weekly_trend > 10:
                recommendations.append('📈 Augmentation des consultations - renforcer le personnel')
            if record.monthly_trend < -5:
                recommendations.append('📉 Baisse des consultations - vérifier les campagnes de prévention')
            
            if not recommendations:
                recommendations.append('✅ Situation stable - continuer la surveillance')
            
            record.ai_recommendations = '<br/>'.join(recommendations)

    def action_refresh_data(self):
        """Actualiser les données du tableau de bord"""
        self._compute_stats()
        self._compute_trends()
        self._compute_alert_level()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_view_students(self):
        """Voir la liste des étudiants"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Étudiants',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('is_student', '=', True)],
        }

    def action_view_active_cases(self):
        """Voir les cas actifs"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cas Actifs',
            'res_model': 'edu.health.record',
            'view_mode': 'tree,form',
            'domain': [('state', '=', 'active')],
        }

    def action_view_vaccinations(self):
        """Voir les vaccinations du jour"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vaccinations du Jour',
            'res_model': 'vaccination.record',
            'view_mode': 'tree,form',
            'domain': [('vaccination_date', '=', fields.Date.today())],
        }

    def action_view_staff(self):
        """Voir le personnel médical"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Personnel Médical',
            'res_model': 'medical.staff',
            'view_mode': 'tree,form',
            'domain': [('is_on_duty', '=', True)],
        }

    def action_generate_report(self):
        """Générer un rapport du tableau de bord"""
        return {
            'type': 'ir.actions.report',
            'report_name': 'edu_health_center.dashboard_report',
            'report_type': 'qweb-pdf',
            'data': {'ids': self.ids},
        } 