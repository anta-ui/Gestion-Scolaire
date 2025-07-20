# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TransportAnalyticsController(http.Controller):

    @http.route('/api/transport/analytics', auth='user', type='json', methods=['POST'])
    def get_transport_analytics(self, **kwargs):
        """
        Endpoint JSON pour récupérer les données d'analyse du transport
        Exemple de body JSON :
        {
            "date_from": "2024-01-01",
            "date_to": "2024-01-31"
        }
        """
        params = request.jsonrequest
        date_from = params.get('date_from')
        date_to = params.get('date_to')

        domain = []
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))

        records = request.env['transport.analytics'].sudo().search(domain)

        data = []
        for r in records:
            data.append({
                'date': r.date,
                'vehicle': r.vehicle_name,
                'driver': r.driver_name,
                'route': r.route_name,
                'distance': r.total_distance,
                'duration': r.total_duration,
                'fuel_consumption': r.fuel_consumption,
                'cost': r.total_cost,
                'speed_avg': r.avg_speed,
                'incidents': r.incident_count,
                'delays': r.delay_count,
            })

        return {'count': len(data), 'results': data}

    @http.route('/api/transport/report/<int:report_id>', auth='user', type='json', methods=['GET'])
    def get_transport_report(self, report_id):
        """Récupérer le contenu HTML du rapport transport"""
        report = request.env['transport.report'].sudo().browse(report_id)
        if not report.exists():
            return {'error': 'Rapport non trouvé'}
        
        return {
            'name': report.name,
            'type': report.report_type,
            'date_from': str(report.date_from),
            'date_to': str(report.date_to),
            'state': report.state,
            'content_html': report.content,
        }

    @http.route('/api/transport/reports', auth='user', type='json', methods=['GET'])
    def list_reports(self):
        """Lister les rapports générés"""
        reports = request.env['transport.report'].sudo().search([], limit=100, order='create_date desc')
        return [{
            'id': r.id,
            'name': r.name,
            'date_from': str(r.date_from),
            'date_to': str(r.date_to),
            'type': r.report_type,
            'state': r.state
        } for r in reports]
