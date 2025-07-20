# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class PortalMenuController(http.Controller):

    @http.route('/api/portal/menus', type='json', auth='user', methods=['GET'])
    def get_portal_menus(self):
        """Récupère les menus accessibles par l'utilisateur connecté"""
        user_groups = request.env.user.groups_id.ids
        domain = [
            ('visible', '=', True),
            ('active', '=', True),
            '|', ('user_groups', '=', False), ('user_groups', 'in', user_groups)
        ]

        menus = request.env['edu.portal.menu'].sudo().search(domain, order='sequence, name')
        
        def get_menu_data(menu):
            return {
                'id': menu.id,
                'name': menu.name,
                'code': menu.code,
                'url': menu.url,
                'icon': menu.icon,
                'target': menu.target,
                'description': menu.description,
                'children': [get_menu_data(child) for child in menu.child_ids.filtered(lambda c: c.visible and c.active)]
            }

        menu_list = [get_menu_data(menu) for menu in menus.filtered(lambda m: not m.parent_id)]

        return {'success': True, 'menus': menu_list}

    @http.route('/api/portal/menus', type='json', auth='user', methods=['POST'])
    def create_portal_menu(self, **kw):
        """Créer un nouveau menu"""
        vals = kw.get('data', {})
        menu = request.env['edu.portal.menu'].sudo().create(vals)
        return {'success': True, 'menu_id': menu.id}

    @http.route('/api/portal/menus/<int:menu_id>', type='json', auth='user', methods=['PUT'])
    def update_portal_menu(self, menu_id, **kw):
        """Mettre à jour un menu existant"""
        vals = kw.get('data', {})
        menu = request.env['edu.portal.menu'].sudo().browse(menu_id)
        if not menu.exists():
            return {'success': False, 'error': 'Menu not found'}
        menu.write(vals)
        return {'success': True}

    @http.route('/api/portal/menus/<int:menu_id>', type='json', auth='user', methods=['DELETE'])
    def delete_portal_menu(self, menu_id):
        """Supprimer un menu"""
        menu = request.env['edu.portal.menu'].sudo().browse(menu_id)
        if not menu.exists():
            return {'success': False, 'error': 'Menu not found'}
        menu.unlink()
        return {'success': True}

    @http.route('/api/portal/menus/<int:menu_id>', type='json', auth='user', methods=['GET'])
    def get_portal_menu_detail(self, menu_id):
        """Récupérer les détails d'un menu"""
        menu = request.env['edu.portal.menu'].sudo().browse(menu_id)
        if not menu.exists():
            return {'success': False, 'error': 'Menu not found'}

        return {
            'success': True,
            'menu': {
                'id': menu.id,
                'name': menu.name,
                'code': menu.code,
                'url': menu.url,
                'icon': menu.icon,
                'target': menu.target,
                'description': menu.description,
                'visible': menu.visible,
                'active': menu.active,
                'sequence': menu.sequence,
                'parent_id': menu.parent_id.id if menu.parent_id else None,
                'child_ids': [child.id for child in menu.child_ids],
            }
        }
