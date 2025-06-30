# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging
import json

_logger = logging.getLogger(__name__)


class TransportAnalytics(models.Model):
    _name = 'transport.analytics'
    _description = 'Analyses Transport'
    _auto = False  # Vue SQL

    # Période d'analyse
    date = fields.Date('Date')
    month = fields.Char('Mois')
    year = fields.Char('Année')
    
    # Véhicule
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule')
    vehicle_name = fields.Char('Nom véhicule')
    
    # Chauffeur
    driver_id = fields.Many2one('transport.driver', 'Chauffeur')
    driver_name = fields.Char('Nom chauffeur')
    
    # Itinéraire
    route_id = fields.Many2one('transport.route', 'Itinéraire')
    route_name = fields.Char('Nom itinéraire')
    
    # Métriques
    total_trips = fields.Integer('Nombre de trajets')
    total_distance = fields.Float('Distance totale (km)')
    total_duration = fields.Float('Durée totale (min)')
    total_students = fields.Integer('Nombre d\'étudiants')
    total_cost = fields.Float('Coût total')
    fuel_consumption = fields.Float('Consommation carburant (L)')
    
    # Ratios
    avg_speed = fields.Float('Vitesse moyenne (km/h)')
    cost_per_km = fields.Float('Coût par km')
    cost_per_student = fields.Float('Coût par étudiant')
    occupancy_rate = fields.Float('Taux d\'occupation (%)')
    
    # Incidents
    incident_count = fields.Integer('Nombre d\'incidents')
    delay_count = fields.Integer('Nombre de retards')
    
    def init(self):
        """Créer la vue SQL pour les analyses"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    t.scheduled_date AS date,
                    TO_CHAR(t.scheduled_date, 'YYYY-MM') AS month,
                    TO_CHAR(t.scheduled_date, 'YYYY') AS year,
                    t.vehicle_id,
                    v.name AS vehicle_name,
                    t.driver_id,
                    d.name AS driver_name,
                    t.route_id,
                    r.name AS route_name,
                    1 AS total_trips,
                    COALESCE(t.distance, 0) AS total_distance,
                    COALESCE(t.duration, 0) AS total_duration,
                    0 AS total_students,
                    COALESCE(t.fuel_cost, 0) AS total_cost,
                    COALESCE(t.fuel_cost, 0) / 1.5 AS fuel_consumption,
                    CASE WHEN COALESCE(t.duration, 0) > 0 THEN COALESCE(t.distance, 0) / (COALESCE(t.duration, 0) / 60) ELSE 0 END AS avg_speed,
                    CASE WHEN COALESCE(t.distance, 0) > 0 THEN COALESCE(t.fuel_cost, 0) / COALESCE(t.distance, 0) ELSE 0 END AS cost_per_km,
                    0 AS cost_per_student,
                    0 AS occupancy_rate,
                    CASE WHEN t.has_incident THEN 1 ELSE 0 END AS incident_count,
                    CASE WHEN t.state = 'delayed' THEN 1 ELSE 0 END AS delay_count
                FROM transport_trip t
                LEFT JOIN transport_vehicle v ON t.vehicle_id = v.id
                LEFT JOIN transport_driver d ON t.driver_id = d.id
                LEFT JOIN transport_route r ON t.route_id = r.id
                WHERE t.state IN ('completed', 'delayed')
            )
        """ % self._table)


class TransportDashboard(models.Model):
    _name = 'transport.dashboard'
    _description = 'Tableau de Bord Transport'

    name = fields.Char('Nom', required=True)
    user_id = fields.Many2one('res.users', 'Utilisateur', default=lambda self: self.env.user)
    
    # Période d'analyse
    date_from = fields.Date('Date de début', required=True, default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date('Date de fin', required=True, default=fields.Date.today)
    
    # Filtres
    vehicle_ids = fields.Many2many('transport.vehicle', string='Véhicules')
    driver_ids = fields.Many2many('transport.driver', string='Chauffeurs')
    route_ids = fields.Many2many('transport.route', string='Itinéraires')
    
    # KPIs calculés
    total_trips = fields.Integer('Total trajets', compute='_compute_kpis')
    total_distance = fields.Float('Distance totale (km)', compute='_compute_kpis')
    total_cost = fields.Float('Coût total', compute='_compute_kpis')
    avg_occupancy = fields.Float('Taux d\'occupation moyen (%)', compute='_compute_kpis')
    incident_rate = fields.Float('Taux d\'incidents (%)', compute='_compute_kpis')
    on_time_rate = fields.Float('Taux de ponctualité (%)', compute='_compute_kpis')
    
    # Graphiques
    chart_data = fields.Text('Données graphiques', compute='_compute_chart_data')
    
    @api.depends('date_from', 'date_to', 'vehicle_ids', 'driver_ids', 'route_ids')
    def _compute_kpis(self):
        for dashboard in self:
            domain = [
                ('scheduled_date', '>=', dashboard.date_from),
                ('scheduled_date', '<=', dashboard.date_to),
                ('state', 'in', ['completed', 'delayed'])
            ]
            
            if dashboard.vehicle_ids:
                domain.append(('vehicle_id', 'in', dashboard.vehicle_ids.ids))
            if dashboard.driver_ids:
                domain.append(('driver_id', 'in', dashboard.driver_ids.ids))
            if dashboard.route_ids:
                domain.append(('route_id', 'in', dashboard.route_ids.ids))
            
            trips = self.env['transport.trip'].search(domain)
            
            dashboard.total_trips = len(trips)
            dashboard.total_distance = sum(trips.mapped('distance'))
            dashboard.total_cost = sum(trips.mapped('total_cost'))
            
            if trips:
                # Taux d'occupation moyen
                occupancy_rates = []
                for trip in trips:
                    if trip.vehicle_id.total_capacity > 0:
                        occupancy_rates.append(trip.passenger_count * 100.0 / trip.vehicle_id.total_capacity)
                dashboard.avg_occupancy = sum(occupancy_rates) / len(occupancy_rates) if occupancy_rates else 0
                
                # Taux d'incidents
                incident_trips = trips.filtered('has_incident')
                dashboard.incident_rate = len(incident_trips) * 100.0 / len(trips)
                
                # Taux de ponctualité
                on_time_trips = trips.filtered(lambda t: t.state == 'completed')
                dashboard.on_time_rate = len(on_time_trips) * 100.0 / len(trips)
            else:
                dashboard.avg_occupancy = 0
                dashboard.incident_rate = 0
                dashboard.on_time_rate = 0
    
    @api.depends('date_from', 'date_to', 'vehicle_ids', 'driver_ids', 'route_ids')
    def _compute_chart_data(self):
        for dashboard in self:
            # Générer les données pour les graphiques
            chart_data = {
                'trips_by_day': dashboard._get_trips_by_day(),
                'cost_by_vehicle': dashboard._get_cost_by_vehicle(),
                'occupancy_by_route': dashboard._get_occupancy_by_route(),
                'incidents_by_type': dashboard._get_incidents_by_type()
            }
            dashboard.chart_data = json.dumps(chart_data)
    
    def _get_trips_by_day(self):
        """Obtenir le nombre de trajets par jour"""
        domain = [
            ('scheduled_date', '>=', self.date_from),
            ('scheduled_date', '<=', self.date_to)
        ]
        
        if self.vehicle_ids:
            domain.append(('vehicle_id', 'in', self.vehicle_ids.ids))
        
        trips = self.env['transport.trip'].read_group(
            domain,
            ['scheduled_date'],
            ['scheduled_date:day']
        )
        
        return [(trip['scheduled_date:day'], trip['scheduled_date_count']) for trip in trips]
    
    def _get_cost_by_vehicle(self):
        """Obtenir les coûts par véhicule"""
        domain = [
            ('scheduled_date', '>=', self.date_from),
            ('scheduled_date', '<=', self.date_to)
        ]
        
        if self.vehicle_ids:
            domain.append(('vehicle_id', 'in', self.vehicle_ids.ids))
        
        trips = self.env['transport.trip'].read_group(
            domain,
            ['vehicle_id', 'total_cost'],
            ['vehicle_id']
        )
        
        result = []
        for trip in trips:
            vehicle = self.env['transport.vehicle'].browse(trip['vehicle_id'][0])
            result.append((vehicle.name, trip['total_cost']))
        
        return result
    
    def _get_occupancy_by_route(self):
        """Obtenir le taux d'occupation par itinéraire"""
        domain = [
            ('scheduled_date', '>=', self.date_from),
            ('scheduled_date', '<=', self.date_to)
        ]
        
        if self.route_ids:
            domain.append(('route_id', 'in', self.route_ids.ids))
        
        trips = self.env['transport.trip'].search(domain)
        route_data = {}
        
        for trip in trips:
            route_name = trip.route_id.name
            if route_name not in route_data:
                route_data[route_name] = {'total_passengers': 0, 'total_capacity': 0, 'trip_count': 0}
            
            route_data[route_name]['total_passengers'] += trip.passenger_count
            route_data[route_name]['total_capacity'] += trip.vehicle_id.total_capacity
            route_data[route_name]['trip_count'] += 1
        
        result = []
        for route_name, data in route_data.items():
            if data['total_capacity'] > 0:
                occupancy = data['total_passengers'] * 100.0 / data['total_capacity']
                result.append((route_name, occupancy))
        
        return result
    
    def _get_incidents_by_type(self):
        """Obtenir les incidents par type"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        
        incidents = self.env['transport.incident'].read_group(
            domain,
            ['incident_type'],
            ['incident_type']
        )
        
        return [(incident['incident_type'], incident['incident_type_count']) for incident in incidents]


class TransportReport(models.Model):
    _name = 'transport.report'
    _description = 'Rapport Transport'

    name = fields.Char('Nom du rapport', required=True)
    report_type = fields.Selection([
        ('daily', 'Rapport quotidien'),
        ('weekly', 'Rapport hebdomadaire'),
        ('monthly', 'Rapport mensuel'),
        ('custom', 'Rapport personnalisé')
    ], string='Type de rapport', required=True, default='daily')
    
    # Période
    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    
    # Contenu du rapport
    content = fields.Html('Contenu', compute='_compute_content')
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('generated', 'Généré'),
        ('sent', 'Envoyé')
    ], default='draft', string='Statut')
    
    @api.depends('report_type', 'date_from', 'date_to')
    def _compute_content(self):
        for report in self:
            if report.report_type == 'daily':
                report.content = report._generate_daily_report()
            elif report.report_type == 'weekly':
                report.content = report._generate_weekly_report()
            elif report.report_type == 'monthly':
                report.content = report._generate_monthly_report()
            else:
                report.content = report._generate_custom_report()
    
    def _generate_daily_report(self):
        """Générer un rapport quotidien"""
        trips = self.env['transport.trip'].search([
            ('scheduled_date', '=', self.date_from),
            ('state', 'in', ['completed', 'delayed', 'cancelled'])
        ])
        
        html = f"""
        <h2>Rapport Quotidien - {self.date_from}</h2>
        <h3>Résumé</h3>
        <ul>
            <li>Nombre total de trajets: {len(trips)}</li>
            <li>Trajets terminés: {len(trips.filtered(lambda t: t.state == 'completed'))}</li>
            <li>Trajets en retard: {len(trips.filtered(lambda t: t.state == 'delayed'))}</li>
            <li>Trajets annulés: {len(trips.filtered(lambda t: t.state == 'cancelled'))}</li>
            <li>Distance totale: {sum(trips.mapped('distance')):.2f} km</li>
            <li>Coût total: {sum(trips.mapped('total_cost')):.2f} €</li>
        </ul>
        """
        
        return html
    
    def _generate_weekly_report(self):
        """Générer un rapport hebdomadaire"""
        trips = self.env['transport.trip'].search([
            ('scheduled_date', '>=', self.date_from),
            ('scheduled_date', '<=', self.date_to),
            ('state', 'in', ['completed', 'delayed', 'cancelled'])
        ])
        
        html = f"""
        <h2>Rapport Hebdomadaire - {self.date_from} au {self.date_to}</h2>
        <h3>Résumé</h3>
        <ul>
            <li>Nombre total de trajets: {len(trips)}</li>
            <li>Distance totale: {sum(trips.mapped('distance')):.2f} km</li>
            <li>Coût total: {sum(trips.mapped('total_cost')):.2f} €</li>
            <li>Nombre d'incidents: {len(trips.filtered('has_incident'))}</li>
        </ul>
        """
        
        return html
    
    def _generate_monthly_report(self):
        """Générer un rapport mensuel"""
        return self._generate_weekly_report()  # Même structure pour l'instant
    
    def _generate_custom_report(self):
        """Générer un rapport personnalisé"""
        return "<h2>Rapport personnalisé</h2><p>À personnaliser selon les besoins.</p>"
    
    def action_generate(self):
        """Générer le rapport"""
        self.state = 'generated'
    
    def action_send(self):
        """Envoyer le rapport par email"""
        self.state = 'sent'
        # Ici on implémenterait l'envoi par email
