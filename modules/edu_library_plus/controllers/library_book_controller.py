# controllers/library_book_api.py

from odoo import http
from odoo.http import request
import base64


class LibraryBookAPI(http.Controller):

    @http.route('/api/library/books', type='json', auth='user', methods=['POST'], csrf=False)
    def list_books(self):
        books = request.env['library.book'].sudo().search([], limit=100)
        return {
            'status': 'success',
            'data': [{
                'id': b.id,
                'title': b.title,
                'isbn': b.isbn,
                'format_type': b.format_type,
                'total_copies': b.total_copies,
                'available_copies': b.available_copies,
                'state': b.state,
            } for b in books]
        }

    @http.route('/api/library/books/<int:book_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_book(self, book_id):
        book = request.env['library.book'].sudo().browse(book_id)
        if not book.exists():
            return {'error': 'Not found'}, 404

        return {
            'id': book.id,
            'title': book.title,
            'subtitle': book.subtitle,
            'isbn': book.isbn,
            'isbn13': book.isbn13,
            'barcode': book.barcode,
            'author_ids': [{'id': a.id, 'name': a.name} for a in book.author_ids],
            'publisher': book.publisher_id.name if book.publisher_id else None,
            'category': book.category_id.name if book.category_id else None,
            'description': book.description,
            'publication_date': str(book.publication_date) if book.publication_date else None,
            'pages': book.pages,
            'language': book.language_id.code if book.language_id else None,
            'format_type': book.format_type,
            'physical_format': book.physical_format,
            'digital_format': book.digital_format,
            'location': book.location,
            'state': book.state,
            'available_copies': book.available_copies,
            'total_copies': book.total_copies,
            'loaned_copies': book.loaned_copies,
            'reserved_copies': book.reserved_copies,
            'purchase_price': book.purchase_price,
            'current_value': book.current_value,
            'replacement_cost': book.replacement_cost,
            'external_url': book.external_url,
            'publisher_url': book.publisher_url,
            'tags': book.tags,
            'age_range': book.age_range,
            'difficulty_level': book.difficulty_level,
            'popularity_score': book.popularity_score,
            'rating_count': book.rating_count,
            'average_rating': book.average_rating,
            'active': book.active,
        }

    @http.route('/api/library/books', type='json', auth='user', methods=['POST'], csrf=False)
    def create_book(self):
        data = request.jsonrequest
        try:
            book = request.env['library.book'].sudo().create({
                'title': data.get('title'),
                'subtitle': data.get('subtitle'),
                'isbn': data.get('isbn'),
                'isbn13': data.get('isbn13'),
                'author_ids': [(6, 0, data.get('author_ids', []))],
                'publisher_id': data.get('publisher_id'),
                'category_id': data.get('category_id'),
                'description': data.get('description'),
                'publication_date': data.get('publication_date'),
                'pages': data.get('pages'),
                'format_type': data.get('format_type', 'physical'),
                'physical_format': data.get('physical_format'),
                'digital_format': data.get('digital_format'),
                'location': data.get('location'),
                'state': data.get('state', 'available'),
                'total_copies': data.get('total_copies', 1),
                'purchase_price': data.get('purchase_price'),
                'external_url': data.get('external_url'),
                'tags': data.get('tags'),
                'age_range': data.get('age_range'),
                'difficulty_level': data.get('difficulty_level'),
            })
            return {'id': book.id, 'message': 'Created'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/books/<int:book_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_book(self, book_id):
        data = request.jsonrequest
        book = request.env['library.book'].sudo().browse(book_id)
        if not book.exists():
            return {'error': 'Not found'}, 404
        try:
            book.write(data)
            return {'message': 'Updated'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/books/<int:book_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_book(self, book_id):
        book = request.env['library.book'].sudo().browse(book_id)
        if not book.exists():
            return {'error': 'Not found'}, 404
        book.unlink()
        return {'message': 'Deleted'}
