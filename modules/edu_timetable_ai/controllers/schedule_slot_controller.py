# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime
import json

class ScheduleSlotController(http.Controller):

    @http.route('/api/schedule_slots', type='json', auth='user', methods=['GET'])
    def get_all_slots(self, **kwargs):
        """Retourne tous les créneaux"""
        slots = request.env['edu.schedule.slot'].sudo().search([])
        return [self._serialize_slot(slot) for slot in slots]

    @http.route('/api/schedule_slots/<int:slot_id>', type='json', auth='user', methods=['GET'])
    def get_slot(self, slot_id):
        """Retourne un créneau spécifique"""
        slot = request.env['edu.schedule.slot'].sudo().browse(slot_id)
        if not slot.exists():
            return {'error': 'Créneau non trouvé'}
        return self._serialize_slot(slot)

    @http.route('/api/schedule_slots', type='json', auth='user', methods=['POST'])
    def create_slot(self, **kwargs):
        """Créer un nouveau créneau"""
        try:
            vals = kwargs.get('data', {})
            slot = request.env['edu.schedule.slot'].sudo().create(vals)
            return {'success': True, 'id': slot.id}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/schedule_slots/<int:slot_id>', type='json', auth='user', methods=['PUT'])
    def update_slot(self, slot_id, **kwargs):
        """Mettre à jour un créneau"""
        slot = request.env['edu.schedule.slot'].sudo().browse(slot_id)
        if not slot.exists():
            return {'error': 'Créneau non trouvé'}
        try:
            vals = kwargs.get('data', {})
            slot.write(vals)
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/schedule_slots/<int:slot_id>', type='json', auth='user', methods=['DELETE'])
    def delete_slot(self, slot_id):
        """Supprimer un créneau"""
        slot = request.env['edu.schedule.slot'].sudo().browse(slot_id)
        if not slot.exists():
            return {'error': 'Créneau non trouvé'}
        slot.unlink()
        return {'success': True}

    def _serialize_slot(self, slot):
        """Format JSON de sortie"""
        return {
            'id': slot.id,
            'timetable_id': slot.timetable_id.id,
            'date': slot.date.isoformat() if slot.date else None,
            'start_time': slot.start_time,
            'end_time': slot.end_time,
            'duration': slot.duration,
            'subject_id': slot.subject_id.id if slot.subject_id else None,
            'teacher_id': slot.teacher_id.id if slot.teacher_id else None,
            'class_id': slot.class_id.id if slot.class_id else None,
            'room_id': slot.room_id.id if slot.room_id else None,
            'lesson_type': slot.lesson_type,
            'state': slot.state,
            'notes': slot.notes,
            'display_name_custom': slot.display_name_custom,
            'time_range': slot.time_range,
        }
