# controllers/library_category_api.py

from odoo import http
from odoo.http import request


class LibraryCategoryAPI(http.Controller):

    @http.route('/api/library/categories', type='json', auth='user', methods=['POST'], csrf=False)
    def list_categories(self):
        categories = request.env['library.book.category'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'parent_id': c.parent_id.id if c.parent_id else None,
                'parent_name': c.parent_id.name if c.parent_id else None,
                'book_count': c.book_count,
                'active': c.active,
            } for c in categories]
        }

    @http.route('/api/library/categories/<int:cat_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_category(self, cat_id):
        category = request.env['library.book.category'].sudo().browse(cat_id)
        if not category.exists():
            return {'error': 'Not found'}, 404
        return {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'parent_id': category.parent_id.id if category.parent_id else None,
            'parent_name': category.parent_id.name if category.parent_id else None,
            'book_count': category.book_count,
            'child_ids': [{'id': c.id, 'name': c.name} for c in category.child_ids],
            'active': category.active,
        }

    @http.route('/api/library/categories', type='json', auth='user', methods=['POST'], csrf=False)
    def create_category(self):
        data = request.jsonrequest
        try:
            category = request.env['library.book.category'].sudo().create({
                'name': data.get('name'),
                'description': data.get('description'),
                'parent_id': data.get('parent_id'),
                'color': data.get('color', 0),
                'active': data.get('active', True)
            })
            return {'id': category.id, 'message': 'Created'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/categories/<int:cat_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_category(self, cat_id):
        data = request.jsonrequest
        category = request.env['library.book.category'].sudo().browse(cat_id)
        if not category.exists():
            return {'error': 'Not found'}, 404
        try:
            category.write(data)
            return {'message': 'Updated'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/categories/<int:cat_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_category(self, cat_id):
        category = request.env['library.book.category'].sudo().browse(cat_id)
        if not category.exists():
            return {'error': 'Not found'}, 404
        try:
            category.unlink()
            return {'message': 'Deleted'}
        except Exception as e:
            return {'error': str(e)}, 400
