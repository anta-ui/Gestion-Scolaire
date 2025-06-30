# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools.translate import _


class CommunicationPortal(CustomerPortal):
    """Contrôleur portal pour la communication"""

    def _prepare_home_portal_values(self, counters):
        """Préparer les valeurs pour la page d'accueil du portail"""
        values = super()._prepare_home_portal_values(counters)
        
        partner = request.env.user.partner_id
        
        if 'message_count' in counters:
            message_count = request.env['edu.message'].search_count([
                ('recipient_ids', 'in', [partner.id])
            ])
            values['message_count'] = message_count
            
        if 'announcement_count' in counters:
            announcement_count = request.env['edu.announcement'].search_count([
                ('is_public', '=', True)
            ])
            values['announcement_count'] = announcement_count
        
        return values

    @http.route(['/my/messages', '/my/messages/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_my_messages(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """Page des messages du portail"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        domain = [('recipient_ids', 'in', [partner.id])]
        
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Sujet'), 'order': 'subject'},
            'status': {'label': _('Statut'), 'order': 'status'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Recherche de messages
        messages = request.env['edu.message'].search(domain, order=order)
        
        values.update({
            'messages': messages,
            'page_name': 'message',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        
        return request.render("edu_communication_hub.portal_my_messages", values)

    @http.route(['/my/message/<int:message_id>'], type='http', auth="user", website=True)
    def portal_message_detail(self, message_id, access_token=None, **kw):
        """Détail d'un message"""
        try:
            message = request.env['edu.message'].browse(message_id)
            partner = request.env.user.partner_id
            
            # Vérifier l'accès
            if partner not in message.recipient_ids:
                return request.not_found()
            
            # Marquer comme lu
            message.write({'read_date': request.env.cr.now()})
            
            values = {
                'message': message,
                'page_name': 'message_detail',
            }
            
            return request.render("edu_communication_hub.portal_message_detail", values)
        except:
            return request.not_found()

    @http.route(['/my/announcements'], type='http', auth="user", website=True)
    def portal_announcements(self, **kw):
        """Page des annonces publiques"""
        announcements = request.env['edu.announcement'].search([
            ('is_public', '=', True),
            ('active', '=', True)
        ], order='create_date desc')
        
        values = {
            'announcements': announcements,
            'page_name': 'announcements',
        }
        
        return request.render("edu_communication_hub.portal_announcements", values)
