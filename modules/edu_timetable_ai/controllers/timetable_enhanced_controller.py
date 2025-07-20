# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class RoomController(http.Controller):

    @http.route('/api/rooms', type='json', auth='user', methods=['GET'])
    def get_rooms(self, **kwargs):
        """ Récupère la liste des salles """
        rooms = request.env['edu.room.enhanced'].sudo().search([])
        return [{
            'id': room.id,
            'name': room.name,
            'code': room.code,
            'building': room.building_id.name if room.building_id else '',
            'capacity': room.capacity,
            'floor': room.floor,
            'state': room.state,
            'room_type': room.room_type,
            'has_projector': room.has_projector,
            'has_internet': room.has_internet,
        } for room in rooms]

    @http.route('/api/rooms/<int:room_id>', type='json', auth='user', methods=['GET'])
    def get_room(self, room_id, **kwargs):
        """ Récupère une salle spécifique par ID """
        room = request.env['edu.room.enhanced'].sudo().browse(room_id)
        if not room.exists():
            return {'error': 'Salle non trouvée'}
        return {
            'id': room.id,
            'name': room.name,
            'code': room.code,
            'building': room.building_id.name if room.building_id else '',
            'capacity': room.capacity,
            'floor': room.floor,
            'state': room.state,
            'room_type': room.room_type,
            'equipment_ids': [eq.name for eq in room.equipment_ids],
            'has_projector': room.has_projector,
            'has_whiteboard': room.has_whiteboard,
            'has_internet': room.has_internet,
        }

    @http.route('/api/rooms', type='json', auth='user', methods=['POST'])
    def create_room(self, **post):
        """ Crée une nouvelle salle """
        vals = post.get('values', {})
        try:
            room = request.env['edu.room.enhanced'].sudo().create(vals)
            return {'id': room.id, 'message': 'Salle créée avec succès'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/rooms/<int:room_id>', type='json', auth='user', methods=['PUT'])
    def update_room(self, room_id, **post):
        """ Met à jour une salle existante """
        room = request.env['edu.room.enhanced'].sudo().browse(room_id)
        if not room.exists():
            return {'error': 'Salle introuvable'}
        try:
            room.write(post.get('values', {}))
            return {'message': 'Salle mise à jour avec succès'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/rooms/<int:room_id>', type='json', auth='user', methods=['DELETE'])
    def delete_room(self, room_id, **kwargs):
        """ Supprime une salle """
        room = request.env['edu.room.enhanced'].sudo().browse(room_id)
        if not room.exists():
            return {'error': 'Salle introuvable'}
        room.unlink()
        return {'message': 'Salle supprimée avec succès'}
