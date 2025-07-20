# controllers/library_loan_api.py

from odoo import http
from odoo.http import request
from datetime import datetime


class LibraryLoanAPI(http.Controller):

    @http.route('/api/library/loans', type='json', auth='user', methods=['POST'], csrf=False)
    def list_loans(self):
        loans = request.env['library.loan'].sudo().search([], limit=100)
        return {
            'status': 'success',
            'data': [{
                'id': l.id,
                'name': l.name,
                'book_id': l.book_id.id,
                'book_title': l.book_id.title,
                'member_id': l.member_id.id,
                'loan_date': str(l.loan_date),
                'due_date': str(l.due_date),
                'return_date': str(l.return_date) if l.return_date else None,
                'state': l.state,
                'is_overdue': l.is_overdue,
                'days_overdue': l.days_overdue
            } for l in loans]
        }

    @http.route('/api/library/loans/<int:loan_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_loan(self, loan_id):
        loan = request.env['library.loan'].sudo().browse(loan_id)
        if not loan.exists():
            return {'error': 'Not found'}, 404
        return {
            'id': loan.id,
            'name': loan.name,
            'book_id': loan.book_id.id,
            'book_title': loan.book_id.title,
            'member_id': loan.member_id.id,
            'loan_date': str(loan.loan_date),
            'due_date': str(loan.due_date),
            'return_date': str(loan.return_date) if loan.return_date else None,
            'state': loan.state,
            'fine_amount': loan.fine_amount,
            'is_overdue': loan.is_overdue,
            'days_overdue': loan.days_overdue,
            'notes': loan.notes,
        }

    @http.route('/api/library/loans', type='json', auth='user', methods=['POST'], csrf=False)
    def create_loan(self):
        data = request.jsonrequest
        try:
            loan = request.env['library.loan'].sudo().create({
                'book_id': data['book_id'],
                'member_id': data['member_id'],
                'loan_date': data.get('loan_date', fields.Datetime.now()),
                'notes': data.get('notes', ''),
            })
            return {'id': loan.id, 'message': 'Created'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/loans/<int:loan_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_loan(self, loan_id):
        data = request.jsonrequest
        loan = request.env['library.loan'].sudo().browse(loan_id)
        if not loan.exists():
            return {'error': 'Not found'}, 404
        try:
            loan.write(data)
            return {'message': 'Updated'}
        except Exception as e:
            return {'error': str(e)}, 400

    @http.route('/api/library/loans/<int:loan_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_loan(self, loan_id):
        loan = request.env['library.loan'].sudo().browse(loan_id)
        if not loan.exists():
            return {'error': 'Not found'}, 404
        loan.unlink()
        return {'message': 'Deleted'}

    # --- Actions Métier ---

    @http.route('/api/library/loans/<int:loan_id>/return', type='json', auth='user', methods=['POST'], csrf=False)
    def return_book(self, loan_id):
        loan = request.env['library.loan'].sudo().browse(loan_id)
        if not loan.exists():
            return {'error': 'Not found'}, 404
        loan.action_return()
        return {'message': 'Returned'}

    @http.route('/api/library/loans/<int:loan_id>/renew', type='json', auth='user', methods=['POST'], csrf=False)
    def renew_loan(self, loan_id):
        loan = request.env['library.loan'].sudo().browse(loan_id)
        if not loan.exists():
            return {'error': 'Not found'}, 404
        loan.action_renew()
        return {'message': 'Renewed', 'new_due_date': str(loan.due_date)}

    @http.route('/api/library/loans/<int:loan_id>/mark_lost', type='json', auth='user', methods=['POST'], csrf=False)
    def mark_lost(self, loan_id):
        loan = request.env['library.loan'].sudo().browse(loan_id)
        if not loan.exists():
            return {'error': 'Not found'}, 404
        loan.action_mark_lost()
        return {'message': 'Marked as lost'}

    @http.route('/api/library/loans/<int:loan_id>/cancel', type='json', auth='user', methods=['POST'], csrf=False)
    def cancel_loan(self, loan_id):
        loan = request.env['library.loan'].sudo().browse(loan_id)
        if not loan.exists():
            return {'error': 'Not found'}, 404
        loan.action_cancel()
        return {'message': 'Cancelled'}
