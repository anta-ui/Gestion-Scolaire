# controllers/library_reservation_api.py

from odoo import http
from odoo.http import request


class LibraryReservationAPI(http.Controller):

    @http.route('/api/library/reservations', type='json', auth='user', methods=['GET'], csrf=False)
    def list_reservations(self):
        reservations = request.env['library.reservation'].sudo().search([], limit=100)
        return [{
            'id': r.id,
            'name': r.name,
            'book': r.book_id.title,
            'member': r.member_id.name,
            'state': r.state,
            'reservation_date': str(r.reservation_date),
            'expiry_date': str(r.expiry_date),
            'priority': r.priority
        } for r in reservations]

    @http.route('/api/library/reservations/<int:res_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_reservation(self, res_id):
        r = request.env['library.reservation'].sudo().browse(res_id)
        if not r.exists():
            return {'error': 'Not found'}, 404
        return {
            'id': r.id,
            'name': r.name,
            'member_id': r.member_id.id,
            'book_id': r.book_id.id,
            'state': r.state,
            'reservation_date': str(r.reservation_date),
            'expiry_date': str(r.expiry_date),
            'collected_date': str(r.collected_date) if r.collected_date else None,
            'priority': r.priority,
            'notes': r.notes,
            'notification_sent': r.notification_sent,
            'loan_id': r.loan_id.id if r.loan_id else None
        }

    @http.route('/api/library/reservations', type='json', auth='user', methods=['POST'], csrf=False)
    def create_reservation(self):
        data = request.jsonrequest
        try:
            r = request.env['library.reservation'].sudo().create({
                'member_id': data['member_id'],
                'book_id': data['book_id'],
                'priority': data.get('priority', 'normal'),
                'notes': data.get('notes', ''),
            })
            return {'id': r.id, 'message': 'Created'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/reservations/<int:res_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_reservation(self, res_id):
        r = request.env['library.reservation'].sudo().browse(res_id)
        if not r.exists():
            return {'error': 'Not found'}, 404
        r.write(request.jsonrequest)
        return {'message': 'Updated'}

    @http.route('/api/library/reservations/<int:res_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_reservation(self, res_id):
        r = request.env['library.reservation'].sudo().browse(res_id)
        if not r.exists():
            return {'error': 'Not found'}, 404
        r.unlink()
        return {'message': 'Deleted'}

    # --- Actions spécifiques ---

    @http.route('/api/library/reservations/<int:res_id>/make_available', type='json', auth='user', methods=['POST'], csrf=False)
    def make_available(self, res_id):
        r = request.env['library.reservation'].sudo().browse(res_id)
        r.action_make_available()
        return {'message': 'Marked as available'}

    @http.route('/api/library/reservations/<int:res_id>/collect', type='json', auth='user', methods=['POST'], csrf=False)
    def collect_reservation(self, res_id):
        r = request.env['library.reservation'].sudo().browse(res_id)
        r.action_collect()
        return {'message': 'Collected', 'loan_id': r.loan_id.id}

    @http.route('/api/library/reservations/<int:res_id>/cancel', type='json', auth='user', methods=['POST'], csrf=False)
    def cancel_reservation(self, res_id):
        r = request.env['library.reservation'].sudo().browse(res_id)
        r.action_cancel()
        return {'message': 'Cancelled'}

    @http.route('/api/library/reservations/<int:res_id>/expire', type='json', auth='user', methods=['POST'], csrf=False)
    def expire_reservation(self, res_id):
        r = request.env['library.reservation'].sudo().browse(res_id)
        r.action_expire()
        return {'message': 'Expired'}
