# controllers/library_author_api.py

from odoo import http
from odoo.http import request
import base64


class LibraryAuthorAPI(http.Controller):

    @http.route('/api/library/authors', type='json', auth='user', methods=['POST'], csrf=False)
    def list_authors(self):
        authors = request.env['library.book.author'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': a.id,
                'name': a.name,
                'first_name': a.first_name,
                'last_name': a.last_name,
                'book_count': a.book_count,
                'nationality': a.nationality.name if a.nationality else None,
                'email': a.email,
                'phone': a.phone,
            } for a in authors]
        }

    @http.route('/api/library/authors/<int:author_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_author(self, author_id):
        a = request.env['library.book.author'].sudo().browse(author_id)
        if not a.exists():
            return {'error': 'Not found'}, 404
        return {
            'id': a.id,
            'name': a.name,
            'first_name': a.first_name,
            'last_name': a.last_name,
            'biography': a.biography,
            'birth_date': str(a.birth_date) if a.birth_date else None,
            'death_date': str(a.death_date) if a.death_date else None,
            'nationality': a.nationality.name if a.nationality else None,
            'website': a.website,
            'email': a.email,
            'phone': a.phone,
            'book_ids': [{'id': b.id, 'title': b.name} for b in a.book_ids],
            'book_count': a.book_count,
            'active': a.active
        }

    @http.route('/api/library/authors', type='json', auth='user', methods=['POST'], csrf=False)
    def create_author(self):
        data = request.jsonrequest
        try:
            author = request.env['library.book.author'].sudo().create({
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'name': data.get('name'),  # Optional, auto-calculated if not present
                'biography': data.get('biography'),
                'birth_date': data.get('birth_date'),
                'death_date': data.get('death_date'),
                'nationality': data.get('nationality_id'),
                'website': data.get('website'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'active': data.get('active', True),
            })
            return {'id': author.id, 'message': 'Created'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/authors/<int:author_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_author(self, author_id):
        data = request.jsonrequest
        author = request.env['library.book.author'].sudo().browse(author_id)
        if not author.exists():
            return {'error': 'Not found'}, 404
        try:
            author.write(data)
            return {'message': 'Updated'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/authors/<int:author_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_author(self, author_id):
        author = request.env['library.book.author'].sudo().browse(author_id)
        if not author.exists():
            return {'error': 'Not found'}, 404
        author.unlink()
        return {'message': 'Deleted'}
