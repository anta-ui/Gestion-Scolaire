# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class ParentDashboardController(http.Controller):

    @http.route('/api/dashboards/data', type='json', auth='user', methods=['GET'])
    def get_dashboard_data(self):
        """Retourne les données complètes du tableau de bord par défaut pour l'utilisateur connecté"""
        dashboard_model = request.env['edu.parent.dashboard'].sudo()
        data = dashboard_model.get_dashboard_data(user_id=request.env.user.id)
        return {'success': True, 'data': data}

    @http.route('/api/dashboards/<int:dashboard_id>/reset', type='json', auth='user', methods=['POST'])
    def reset_dashboard_layout(self, dashboard_id):
        """Réinitialise la disposition du tableau de bord"""
        dashboard = request.env['edu.parent.dashboard'].sudo().browse(dashboard_id)
        if not dashboard.exists():
            return {'success': False, 'error': 'Dashboard not found'}

        dashboard.action_reset_layout()
        return {'success': True}

    @http.route('/api/dashboards/<int:dashboard_id>/duplicate', type='json', auth='user', methods=['POST'])
    def duplicate_dashboard(self, dashboard_id):
        """Duplique le tableau de bord"""
        dashboard = request.env['edu.parent.dashboard'].sudo().browse(dashboard_id)
        if not dashboard.exists():
            return {'success': False, 'error': 'Dashboard not found'}

        new_dashboard = dashboard.copy({
            'name': f"{dashboard.name} (Copie)",
            'is_default': False
        })
        return {
            'success': True,
            'new_dashboard_id': new_dashboard.id,
            'name': new_dashboard.name
        }

    @http.route('/api/dashboards/<int:dashboard_id>', type='json', auth='user', methods=['PUT'])
    def update_dashboard(self, dashboard_id, **kw):
        """Met à jour la configuration d'un tableau de bord"""
        dashboard = request.env['edu.parent.dashboard'].sudo().browse(dashboard_id)
        if not dashboard.exists():
            return {'success': False, 'error': 'Dashboard not found'}

        vals = kw.get('data', {})
        dashboard.write(vals)
        return {'success': True}

    @http.route('/api/dashboards', type='json', auth='user', methods=['POST'])
    def create_dashboard(self, **kw):
        """Créer un nouveau tableau de bord"""
        vals = kw.get('data', {})
        vals['user_id'] = request.env.user.id
        dashboard = request.env['edu.parent.dashboard'].sudo().create(vals)
        return {'success': True, 'dashboard_id': dashboard.id, 'name': dashboard.name}

    @http.route('/api/dashboards/<int:dashboard_id>', type='json', auth='user', methods=['DELETE'])
    def delete_dashboard(self, dashboard_id):
        """Supprime un tableau de bord"""
        dashboard = request.env['edu.parent.dashboard'].sudo().browse(dashboard_id)
        if not dashboard.exists():
            return {'success': False, 'error': 'Dashboard not found'}

        if dashboard.is_default:
            return {'success': False, 'error': 'Cannot delete default dashboard'}

        dashboard.unlink()
        return {'success': True}
