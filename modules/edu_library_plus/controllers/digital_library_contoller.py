# controllers/digital_library_api.py

from odoo import http
from odoo.http import request, Response
import json
import base64


class DigitalLibraryAPI(http.Controller):

    @http.route('/api/digital/library', type='json', auth='user', methods=['GET'], csrf=False)
    def list_libraries(self):
        records = request.env['digital.library'].sudo().search([])
        return [{'id': rec.id, 'name': rec.name, 'file_name': rec.file_name} for rec in records]

    @http.route('/api/digital/library/<int:rec_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_library(self, rec_id):
        record = request.env['digital.library'].sudo().browse(rec_id)
        if not record.exists():
            return {'error': 'Not found'}, 404
        return {
            'id': record.id,
            'name': record.name,
            'book_id': record.book_id.id,
            'file_name': record.file_name,
            'file_type': record.file_type,
            'access_level': record.access_level,
            'is_downloadable': record.is_downloadable,
            'is_readable_online': record.is_readable_online,
            'description': record.description,
            'download_url': f'/web/content/{record.id}/file_data/{record.file_name}?download=true'
        }

    @http.route('/api/digital/library', type='json', auth='user', methods=['POST'], csrf=False)
    def create_library(self, **kwargs):
        data = request.jsonrequest
        try:
            new_record = request.env['digital.library'].sudo().create({
                'name': data['name'],
                'book_id': data['book_id'],
                'file_name': data['file_name'],
                'file_data': data['file_data'],  # base64
                'access_level': data.get('access_level', 'members'),
                'description': data.get('description', ''),
                'is_downloadable': data.get('is_downloadable', True),
                'is_readable_online': data.get('is_readable_online', True),
            })
            return {'id': new_record.id, 'message': 'Created'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/digital/library/<int:rec_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_library(self, rec_id, **kwargs):
        data = request.jsonrequest
        record = request.env['digital.library'].sudo().browse(rec_id)
        if not record.exists():
            return {'error': 'Not found'}, 404
        record.write(data)
        return {'message': 'Updated'}

    @http.route('/api/digital/library/<int:rec_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_library(self, rec_id):
        record = request.env['digital.library'].sudo().browse(rec_id)
        if not record.exists():
            return {'error': 'Not found'}, 404
        record.unlink()
        return {'message': 'Deleted'}
