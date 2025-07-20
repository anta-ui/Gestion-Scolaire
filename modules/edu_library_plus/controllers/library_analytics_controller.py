# controllers/library_analytics_api.py

from odoo import http
from odoo.http import request


class LibraryAnalyticsAPI(http.Controller):

    @http.route('/api/library/analytics', type='json', auth='user', methods=['GET'], csrf=False)
    def list_analytics(self):
        records = request.env['library.analytics'].sudo().search([], limit=1000)
        return [{
            'id': rec.id,
            'name': rec.name,
            'book_id': rec.book_id.id,
            'member_id': rec.member_id.id,
            'loan_count': rec.loan_count,
            'reservation_count': rec.reservation_count,
            'date': rec.date.strftime('%Y-%m-%d')
        } for rec in records]

    @http.route('/api/library/analytics/<int:rec_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_analytics(self, rec_id):
        rec = request.env['library.analytics'].sudo().browse(rec_id)
        if not rec.exists():
            return {'error': 'Not found'}, 404
        return {
            'id': rec.id,
            'name': rec.name,
            'book_id': rec.book_id.id,
            'member_id': rec.member_id.id,
            'loan_count': rec.loan_count,
            'reservation_count': rec.reservation_count,
            'date': rec.date.strftime('%Y-%m-%d')
        }
class LibraryReportAPI(http.Controller):

    @http.route('/api/library/report', type='json', auth='user', methods=['POST'], csrf=False)
    def generate_report(self):
        data = request.jsonrequest
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        report_type = data.get('report_type', 'loans')

        report = request.env['library.report'].sudo().create({
            'date_from': date_from,
            'date_to': date_to,
            'report_type': report_type,
        })

        result_action = report.generate_report()

        # Pour simplifier l'API, on va extraire les enregistrements selon le type
        model = result_action['res_model']
        domain = result_action.get('domain', [])
        records = request.env[model].sudo().search(domain, limit=100)

        return {
            'report_name': result_action['name'],
            'records': [
                {'id': r.id, 'display_name': r.display_name}
                for r in records
            ]
        }