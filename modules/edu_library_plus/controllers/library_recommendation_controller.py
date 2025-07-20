# controllers/library_recommendation_api.py

from odoo import http
from odoo.http import request


class LibraryRecommendationAPI(http.Controller):

    @http.route('/api/library/recommendations', type='json', auth='user', methods=['GET'], csrf=False)
    def list_recommendations(self):
        recs = request.env['library.recommendation'].sudo().search([], limit=100)
        return [{
            'id': r.id,
            'member': r.member_id.name,
            'book': r.book_id.title,
            'status': r.status,
            'score': r.recommendation_score,
        } for r in recs]

    @http.route('/api/library/recommendations/<int:rec_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_recommendation(self, rec_id):
        rec = request.env['library.recommendation'].sudo().browse(rec_id)
        if not rec.exists():
            return {'error': 'Not found'}, 404
        return {
            'id': rec.id,
            'name': rec.name,
            'member_id': rec.member_id.id,
            'book_id': rec.book_id.id,
            'recommended_by': rec.recommended_by,
            'recommendation_score': rec.recommendation_score,
            'reason': rec.reason,
            'status': rec.status,
            'viewed_date': str(rec.viewed_date) if rec.viewed_date else None,
            'response_date': str(rec.response_date) if rec.response_date else None,
            'notes': rec.notes,
        }

    @http.route('/api/library/recommendations', type='json', auth='user', methods=['POST'], csrf=False)
    def create_recommendation(self):
        data = request.jsonrequest
        try:
            rec = request.env['library.recommendation'].sudo().create({
                'member_id': data['member_id'],
                'book_id': data['book_id'],
                'recommended_by': data.get('recommended_by', 'system'),
                'recommendation_score': data.get('recommendation_score', 0.0),
                'reason': data.get('reason', ''),
            })
            return {'id': rec.id, 'message': 'Created'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/recommendations/<int:rec_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_recommendation(self, rec_id):
        rec = request.env['library.recommendation'].sudo().browse(rec_id)
        if not rec.exists():
            return {'error': 'Not found'}, 404
        rec.write(request.jsonrequest)
        return {'message': 'Updated'}

    @http.route('/api/library/recommendations/<int:rec_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_recommendation(self, rec_id):
        rec = request.env['library.recommendation'].sudo().browse(rec_id)
        if not rec.exists():
            return {'error': 'Not found'}, 404
        rec.unlink()
        return {'message': 'Deleted'}

    # --- Actions Métiers ---

    @http.route('/api/library/recommendations/<int:rec_id>/mark_viewed', type='json', auth='user', methods=['POST'], csrf=False)
    def mark_viewed(self, rec_id):
        rec = request.env['library.recommendation'].sudo().browse(rec_id)
        rec.action_mark_viewed()
        return {'message': 'Marked as viewed'}

    @http.route('/api/library/recommendations/<int:rec_id>/accept', type='json', auth='user', methods=['POST'], csrf=False)
    def accept_recommendation(self, rec_id):
        rec = request.env['library.recommendation'].sudo().browse(rec_id)
        rec.action_accept()
        return {'message': 'Accepted'}

    @http.route('/api/library/recommendations/<int:rec_id>/reject', type='json', auth='user', methods=['POST'], csrf=False)
    def reject_recommendation(self, rec_id):
        rec = request.env['library.recommendation'].sudo().browse(rec_id)
        rec.action_reject()
        return {'message': 'Rejected'}

    @http.route('/api/library/recommendations/<int:rec_id>/loan', type='json', auth='user', methods=['POST'], csrf=False)
    def loan_book_from_recommendation(self, rec_id):
        rec = request.env['library.recommendation'].sudo().browse(rec_id)
        rec.action_loan_book()
        return {'message': 'Book loan initiated'}
class LibraryRecommendationEngineAPI(http.Controller):

    @http.route('/api/library/recommendation_engines', type='json', auth='user', methods=['GET'], csrf=False)
    def list_engines(self):
        engines = request.env['library.recommendation.engine'].sudo().search([('is_active', '=', True)])
        return [{
            'id': e.id,
            'name': e.name,
            'type': e.algorithm_type,
            'weight': e.weight
        } for e in engines]

    @http.route('/api/library/recommendations/generate', type='json', auth='user', methods=['POST'], csrf=False)
    def generate_recommendations(self):
        data = request.jsonrequest
        member_id = data.get('member_id')
        limit = data.get('limit', 10)

        if not member_id:
            return {'error': 'member_id is required'}, 400

        engine = request.env['library.recommendation.engine'].sudo().search([
            ('is_active', '=', True)
        ], limit=1, order='weight desc')

        if not engine:
            return {'error': 'No active recommendation engine found'}, 400

        result = engine.generate_recommendations(member_id, limit=limit)
        return {'engine': engine.name, 'recommendations': result}