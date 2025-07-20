# controllers/library_publisher_api.py

from odoo import http
from odoo.http import request


class LibraryPublisherAPI(http.Controller):

    @http.route('/api/library/publishers', type='json', auth='user', methods=['GET'], csrf=False)
    def list_publishers(self):
        publishers = request.env['library.book.publisher'].sudo().search([])
        return [{
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'city': p.city,
            'country': p.country_id.name if p.country_id else None,
            'book_count': p.book_count,
            'website': p.website,
            'email': p.email,
            'phone': p.phone,
        } for p in publishers]

    @http.route('/api/library/publishers/<int:publisher_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_publisher(self, publisher_id):
        p = request.env['library.book.publisher'].sudo().browse(publisher_id)
        if not p.exists():
            return {'error': 'Not found'}, 404
        return {
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'address': p.address,
            'city': p.city,
            'state': p.state_id.name if p.state_id else None,
            'country': p.country_id.name if p.country_id else None,
            'zip': p.zip,
            'phone': p.phone,
            'email': p.email,
            'website': p.website,
            'contact_person': p.contact_person,
            'founded_year': p.founded_year,
            'description': p.description,
            'book_count': p.book_count,
            'book_ids': [{'id': b.id, 'title': b.title} for b in p.book_ids],
            'active': p.active
        }

    @http.route('/api/library/publishers', type='json', auth='user', methods=['POST'], csrf=False)
    def create_publisher(self):
        data = request.jsonrequest
        try:
            p = request.env['library.book.publisher'].sudo().create({
                'name': data.get('name'),
                'code': data.get('code'),
                'address': data.get('address'),
                'city': data.get('city'),
                'state_id': data.get('state_id'),
                'country_id': data.get('country_id'),
                'zip': data.get('zip'),
                'phone': data.get('phone'),
                'email': data.get('email'),
                'website': data.get('website'),
                'contact_person': data.get('contact_person'),
                'founded_year': data.get('founded_year'),
                'description': data.get('description'),
                'active': data.get('active', True)
            })
            return {'id': p.id, 'message': 'Created'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/publishers/<int:publisher_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_publisher(self, publisher_id):
        p = request.env['library.book.publisher'].sudo().browse(publisher_id)
        if not p.exists():
            return {'error': 'Not found'}, 404
        try:
            p.write(request.jsonrequest)
            return {'message': 'Updated'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/publishers/<int:publisher_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_publisher(self, publisher_id):
        p = request.env['library.book.publisher'].sudo().browse(publisher_id)
        if not p.exists():
            return {'error': 'Not found'}, 404
        p.unlink()
        return {'message': 'Deleted'}
