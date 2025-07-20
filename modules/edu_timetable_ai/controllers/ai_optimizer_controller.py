# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class AIOptimizerController(http.Controller):

    @http.route('/api/optimizer/start', type='json', auth='user', methods=['POST'])
    def start_optimization(self, optimizer_id):
        """Démarrer une optimisation spécifique"""
        optimizer = request.env['edu.ai.optimizer'].sudo().browse(optimizer_id)
        if not optimizer.exists():
            return {'success': False, 'error': 'Optimizer not found'}
        
        try:
            optimizer.action_start_optimization()
            return {'success': True, 'state': optimizer.state}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/optimizer/<int:optimizer_id>/results', type='json', auth='user', methods=['GET'])
    def optimizer_results(self, optimizer_id):
        """Récupérer les résultats d'une optimisation"""
        optimizer = request.env['edu.ai.optimizer'].sudo().browse(optimizer_id)
        if not optimizer.exists():
            return {'success': False, 'error': 'Optimizer not found'}

        return {
            'success': True,
            'results': {
                'name': optimizer.name,
                'state': optimizer.state,
                'initial_score': optimizer.initial_score,
                'final_score': optimizer.final_score,
                'improvement': optimizer.improvement,
                'duration': optimizer.duration,
                'generations_completed': optimizer.generations_completed,
                'constraint_violations': optimizer.constraint_violations,
                'best_solution': json.loads(optimizer.best_solution or '{}'),
            }
        }

    @http.route('/api/optimizer/history', type='json', auth='user', methods=['GET'])
    def optimization_history(self, **kw):
        """Liste l'historique des optimisations"""
        domain = []
        timetable_id = kw.get('timetable_id')
        if timetable_id:
            domain.append(('timetable_id', '=', timetable_id))

        optimizations = request.env['edu.ai.optimizer'].sudo().search(domain, order='start_time desc')

        result = [{
            'id': opt.id,
            'name': opt.name,
            'timetable': opt.timetable_id.name,
            'state': opt.state,
            'start_time': opt.start_time,
            'end_time': opt.end_time,
            'improvement': opt.improvement,
            'final_score': opt.final_score,
        } for opt in optimizations]

        return {'success': True, 'history': result}

    @http.route('/api/optimizer/<int:optimizer_id>/stop', type='json', auth='user', methods=['POST'])
    def stop_optimization(self, optimizer_id):
        """Arrêter une optimisation en cours (implémentation nécessaire côté serveur)"""
        optimizer = request.env['edu.ai.optimizer'].sudo().browse(optimizer_id)
        if not optimizer.exists():
            return {'success': False, 'error': 'Optimizer not found'}

        # Exemple de mise à jour d'état en cas d'arrêt forcé
        optimizer.sudo().write({
            'state': 'failed',
            'end_time': fields.Datetime.now(),
            'optimization_log': 'Optimisation arrêtée par l\'utilisateur.'
        })

        return {'success': True, 'state': optimizer.state}

    @http.route('/api/optimizer/auto_optimize_all', type='json', auth='user', methods=['POST'])
    def auto_optimize_all(self):
        """Lancer l'auto-optimisation sur tous les emplois du temps éligibles"""
        try:
            count = request.env['edu.ai.optimizer'].sudo().auto_optimize_all_timetables()
            return {'success': True, 'optimized_count': count}
        except Exception as e:
            return {'success': False, 'error': str(e)}
