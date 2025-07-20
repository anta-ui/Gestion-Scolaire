# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class EduCompetencyController(http.Controller):

    # === COMPÉTENCES ===

    @http.route('/api/competency', type='json', auth='user')
    def get_competencies(self):
        records = request.env['edu.competency'].search([])
        data = records.read(['id', 'name', 'code', 'description', 'competency_type', 'coefficient', 'category_id'])
        return {'status': 200, 'competencies': data}

    @http.route('/api/competency/<int:comp_id>', type='json', auth='user')
    def get_competency(self, comp_id):
        record = request.env['edu.competency'].browse(comp_id)
        if record.exists():
            return {'status': 200, 'competency': record.read()[0]}
        return {'status': 404, 'error': 'Compétence non trouvée'}

    @http.route('/api/competency', type='json', auth='user', methods=['POST'])
    def create_competency(self, **kwargs):
        try:
            record = request.env['edu.competency'].create(kwargs)
            return {'status': 201, 'id': record.id}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/competency/<int:comp_id>', type='json', auth='user', methods=['PUT'])
    def update_competency(self, comp_id, **kwargs):
        record = request.env['edu.competency'].browse(comp_id)
        if not record.exists():
            return {'status': 404, 'error': 'Compétence non trouvée'}
        try:
            record.write(kwargs)
            return {'status': 200, 'message': 'Compétence mise à jour'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/competency/<int:comp_id>', type='json', auth='user', methods=['DELETE'])
    def delete_competency(self, comp_id):
        record = request.env['edu.competency'].browse(comp_id)
        if not record.exists():
            return {'status': 404, 'error': 'Compétence non trouvée'}
        record.unlink()
        return {'status': 200, 'message': 'Compétence supprimée'}

    # === CATÉGORIES ===

    @http.route('/api/competency/categories', type='json', auth='user')
    def get_categories(self):
        records = request.env['edu.competency.category'].search([])
        data = records.read(['id', 'name', 'code', 'description'])
        return {'status': 200, 'categories': data}

    # === NIVEAUX DE MAÎTRISE ===

    @http.route('/api/competency/<int:comp_id>/levels', type='json', auth='user')
    def get_mastery_levels(self, comp_id):
        comp = request.env['edu.competency'].browse(comp_id)
        if not comp.exists():
            return {'status': 404, 'error': 'Compétence non trouvée'}
        levels = comp.mastery_level_ids.read(['id', 'name', 'min_score', 'max_score', 'description', 'color_class'])
        return {'status': 200, 'levels': levels}
