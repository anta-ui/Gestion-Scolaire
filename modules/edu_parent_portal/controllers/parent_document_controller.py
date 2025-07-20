# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class ParentDocumentController(http.Controller):

    @http.route('/api/documents', type='json', auth='user', methods=['POST'])
    def create_document(self, **kw):
        """Créer un nouveau document"""
        vals = kw.get('data', {})
        document = request.env['edu.parent.document'].sudo().create(vals)
        return {'success': True, 'document_id': document.id}

    @http.route('/api/documents/<int:document_id>/publish', type='json', auth='user', methods=['POST'])
    def publish_document(self, document_id):
        """Publier un document"""
        document = request.env['edu.parent.document'].sudo().browse(document_id)
        if not document.exists():
            return {'success': False, 'error': 'Document not found'}
        document.action_publish()
        return {'success': True, 'publish_date': document.publish_date}

    @http.route('/api/documents/<int:document_id>', type='json', auth='user', methods=['GET'])
    def get_document(self, document_id):
        """Récupérer les détails d'un document"""
        document = request.env['edu.parent.document'].sudo().browse(document_id)
        if not document.exists():
            return {'success': False, 'error': 'Document not found'}

        return {
            'success': True,
            'document': {
                'id': document.id,
                'name': document.name,
                'type': document.document_type,
                'category': document.category,
                'state': document.state,
                'attachment_url': f'/web/content/{document.attachment_id.id}?download=true',
            }
        }

    @http.route('/api/documents/<int:document_id>', type='json', auth='user', methods=['DELETE'])
    def delete_document(self, document_id):
        """Supprimer un document"""
        document = request.env['edu.parent.document'].sudo().browse(document_id)
        if not document.exists():
            return {'success': False, 'error': 'Document not found'}
        document.unlink()
        return {'success': True}

    @http.route('/api/documents/request', type='json', auth='user', methods=['POST'])
    def request_document(self, **kw):
        """Soumettre une demande de document"""
        vals = kw.get('data', {})
        vals['parent_id'] = request.env.user.partner_id.id
        doc_request = request.env['edu.document.request'].sudo().create(vals)
        doc_request.action_submit()
        return {'success': True, 'request_id': doc_request.id, 'state': doc_request.state}

    @http.route('/api/documents/request/<int:request_id>/state', type='json', auth='user', methods=['PUT'])
    def update_request_state(self, request_id, **kw):
        """Mettre à jour l'état d'une demande de document"""
        new_state = kw.get('state')
        request_rec = request.env['edu.document.request'].sudo().browse(request_id)
        if not request_rec.exists():
            return {'success': False, 'error': 'Request not found'}

        valid_states = ['processing', 'ready', 'delivered', 'cancelled']
        if new_state not in valid_states:
            return {'success': False, 'error': 'Invalid state'}

        getattr(request_rec, f'action_{new_state}')()
        return {'success': True, 'new_state': request_rec.state}

    @http.route('/api/documents/list', type='json', auth='user', methods=['POST'])
    def list_documents(self, **kw):
        """Lister les documents accessibles à l'utilisateur"""
        partner_id = request.env.user.partner_id.id
        documents = request.env['edu.parent.document'].sudo().search([
            ('parent_ids', 'in', [partner_id]),
            ('state', '=', 'published')
        ])
        result = [{
            'id': doc.id,
            'name': doc.name,
            'type': doc.document_type,
            'category': doc.category,
            'publish_date': doc.publish_date,
            'attachment_url': f'/web/content/{doc.attachment_id.id}?download=true',
        } for doc in documents]

        return {'success': True, 'documents': result}
