# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class EduReportCardAPI(http.Controller):

    @http.route('/api/report_cards', type='json', auth='user', methods=['GET'], csrf=False)
    def get_report_cards(self, **kwargs):
        """Liste des bulletins"""
        report_cards = request.env['edu.report.card'].sudo().search([])
        return [{
            'id': rc.id,
            'student': rc.student_id.name,
            'period': rc.period_id.name,
            'batch': rc.batch_id.name,
            'average': rc.general_average,
            'rank': rc.general_rank,
            'state': rc.state,
        } for rc in report_cards]

    @http.route('/api/report_card/<int:rc_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_report_card(self, rc_id, **kwargs):
        """Détails d'un bulletin"""
        rc = request.env['edu.report.card'].sudo().browse(rc_id)
        if not rc.exists():
            return {'error': 'Bulletin introuvable'}
        return {
            'id': rc.id,
            'student': rc.student_id.name,
            'period': rc.period_id.name,
            'batch': rc.batch_id.name,
            'average': rc.general_average,
            'rank': rc.general_rank,
            'lines': [{
                'subject': line.course_id.name,
                'average': line.average,
                'coefficient': line.coefficient,
                'letter': line.grade_letter
            } for line in rc.subject_line_ids],
            'competencies': [{
                'competency': line.competency_id.name,
                'score': line.score,
                'level': line.mastery_level
            } for line in rc.competency_line_ids]
        }

    @http.route('/api/report_card', type='json', auth='user', methods=['POST'], csrf=False)
    def create_report_card(self, **kwargs):
        """Création d'un bulletin"""
        data = request.jsonrequest
        try:
            rc = request.env['edu.report.card'].sudo().create({
                'student_id': data.get('student_id'),
                'batch_id': data.get('batch_id'),
                'period_id': data.get('period_id'),
                'report_type': data.get('report_type', 'standard')
            })
            return {'id': rc.id, 'message': 'Bulletin créé'}
        except Exception as e:
            _logger.error("Erreur création bulletin: %s", str(e))
            return {'error': str(e)}

    @http.route('/api/report_card/<int:rc_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_report_card(self, rc_id, **kwargs):
        """Mise à jour d'un bulletin"""
        data = request.jsonrequest
        rc = request.env['edu.report.card'].sudo().browse(rc_id)
        if not rc.exists():
            return {'error': 'Bulletin introuvable'}
        rc.write(data)
        return {'success': True}

    @http.route('/api/report_card/<int:rc_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_report_card(self, rc_id, **kwargs):
        """Suppression d'un bulletin"""
        rc = request.env['edu.report.card'].sudo().browse(rc_id)
        if not rc.exists():
            return {'error': 'Bulletin introuvable'}
        rc.unlink()
        return {'success': True}
