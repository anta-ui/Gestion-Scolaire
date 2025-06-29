# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EduEvaluationAnalytics(models.Model):
    """Analytiques et statistiques des évaluations"""
    _name = 'edu.evaluation.analytics'
    _description = 'Analytiques d\'évaluation'
    _auto = False
    _rec_name = 'student_name'

    # Dimensions
    student_id = fields.Many2one('op.student', string='Élève', readonly=True)
    student_name = fields.Char(string='Nom de l\'élève', readonly=True)
    course_id = fields.Many2one('op.course', string='Matière', readonly=True)
    course_name = fields.Char(string='Nom de la matière', readonly=True)
    faculty_id = fields.Many2one('op.faculty', string='Enseignant', readonly=True)
    faculty_name = fields.Char(string='Nom de l\'enseignant', readonly=True)
    batch_id = fields.Many2one('op.batch', string='Groupe', readonly=True)
    batch_name = fields.Char(string='Nom du groupe', readonly=True)
    evaluation_type_id = fields.Many2one('edu.evaluation.type', string='Type d\'évaluation', readonly=True)
    evaluation_type_name = fields.Char(string='Type d\'évaluation', readonly=True)
    period_id = fields.Many2one('edu.evaluation.period', string='Période', readonly=True)
    period_name = fields.Char(string='Période', readonly=True)
    
    # Dates
    evaluation_date = fields.Date(string='Date d\'évaluation', readonly=True)
    year = fields.Integer(string='Année', readonly=True)
    month = fields.Integer(string='Mois', readonly=True)
    week = fields.Integer(string='Semaine', readonly=True)
    
    # Métriques
    evaluation_count = fields.Integer(string='Nombre d\'évaluations', readonly=True)
    total_grade = fields.Float(string='Total des notes', readonly=True, digits=(12, 2))
    average_grade = fields.Float(string='Note moyenne', readonly=True, digits=(6, 2))
    min_grade = fields.Float(string='Note minimale', readonly=True, digits=(6, 2))
    max_grade = fields.Float(string='Note maximale', readonly=True, digits=(6, 2))
    grade_percentage = fields.Float(string='Pourcentage moyen', readonly=True, digits=(6, 2))
    
    # Compteurs d'état
    passed_count = fields.Integer(string='Nombre de réussites', readonly=True)
    failed_count = fields.Integer(string='Nombre d\'échecs', readonly=True)
    absent_count = fields.Integer(string='Nombre d\'absences', readonly=True)
    retake_count = fields.Integer(string='Nombre de rattrapages', readonly=True)
    
    # Taux de réussite
    success_rate = fields.Float(string='Taux de réussite (%)', readonly=True, digits=(5, 2))
    absence_rate = fields.Float(string='Taux d\'absence (%)', readonly=True, digits=(5, 2))
    
    def init(self):
        """Initialise la vue SQL pour les analytiques"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    e.student_id,
                    rp_student.name AS student_name,
                    e.course_id,
                    c.name AS course_name,
                    e.faculty_id,
                    rp_faculty.name AS faculty_name,
                    e.batch_id,
                    b.name AS batch_name,
                    e.evaluation_type_id,
                    et.name AS evaluation_type_name,
                    e.period_id,
                    p.name AS period_name,
                    e.date AS evaluation_date,
                    EXTRACT(YEAR FROM e.date) AS year,
                    EXTRACT(MONTH FROM e.date) AS month,
                    EXTRACT(WEEK FROM e.date) AS week,
                    COUNT(e.id) AS evaluation_count,
                    SUM(e.grade) AS total_grade,
                    AVG(e.grade) AS average_grade,
                    MIN(e.grade) AS min_grade,
                    MAX(e.grade) AS max_grade,
                    AVG(e.grade_percentage) AS grade_percentage,
                    SUM(CASE WHEN e.grade_percentage >= 50 AND NOT e.is_absent THEN 1 ELSE 0 END) AS passed_count,
                    SUM(CASE WHEN e.grade_percentage < 50 AND NOT e.is_absent THEN 1 ELSE 0 END) AS failed_count,
                    SUM(CASE WHEN e.is_absent THEN 1 ELSE 0 END) AS absent_count,
                    SUM(CASE WHEN e.is_retake THEN 1 ELSE 0 END) AS retake_count,
                    CASE 
                        WHEN COUNT(e.id) - SUM(CASE WHEN e.is_absent THEN 1 ELSE 0 END) > 0 
                        THEN (SUM(CASE WHEN e.grade_percentage >= 50 AND NOT e.is_absent THEN 1 ELSE 0 END) * 100.0) / 
                             (COUNT(e.id) - SUM(CASE WHEN e.is_absent THEN 1 ELSE 0 END))
                        ELSE 0
                    END AS success_rate,
                    CASE 
                        WHEN COUNT(e.id) > 0 
                        THEN (SUM(CASE WHEN e.is_absent THEN 1 ELSE 0 END) * 100.0) / COUNT(e.id)
                        ELSE 0
                    END AS absence_rate
                FROM edu_evaluation e
                LEFT JOIN op_student s ON e.student_id = s.id
                LEFT JOIN res_partner rp_student ON s.partner_id = rp_student.id
                LEFT JOIN op_course c ON e.course_id = c.id
                LEFT JOIN op_faculty f ON e.faculty_id = f.id
                LEFT JOIN res_partner rp_faculty ON f.partner_id = rp_faculty.id
                LEFT JOIN op_batch b ON e.batch_id = b.id
                LEFT JOIN edu_evaluation_type et ON e.evaluation_type_id = et.id
                LEFT JOIN edu_evaluation_period p ON e.period_id = p.id
                WHERE e.state IN ('confirmed', 'published')
                GROUP BY
                    e.student_id, rp_student.name,
                    e.course_id, c.name,
                    e.faculty_id, rp_faculty.name,
                    e.batch_id, b.name,
                    e.evaluation_type_id, et.name,
                    e.period_id, p.name,
                    e.date,
                    EXTRACT(YEAR FROM e.date),
                    EXTRACT(MONTH FROM e.date),
                    EXTRACT(WEEK FROM e.date)
            )
        """ % self._table)


class EduEvaluationDashboard(models.Model):
    """Tableau de bord des évaluations"""
    _name = 'edu.evaluation.dashboard'
    _description = 'Tableau de bord des évaluations'
    _rec_name = 'name'

    name = fields.Char(string='Nom du tableau de bord', required=True)
    description = fields.Text(string='Description')
    
    # Filtres
    student_ids = fields.Many2many('op.student', string='Élèves')
    course_ids = fields.Many2many('op.course', string='Matières')
    batch_ids = fields.Many2many('op.batch', string='Groupes')
    faculty_ids = fields.Many2many('op.faculty', string='Enseignants')
    period_ids = fields.Many2many('edu.evaluation.period', string='Périodes')
    
    date_from = fields.Date(string='Date de début')
    date_to = fields.Date(string='Date de fin')
    
    # Métriques calculées
    total_evaluations = fields.Integer(string='Total évaluations', compute='_compute_metrics')
    average_grade = fields.Float(string='Note moyenne', compute='_compute_metrics', digits=(6, 2))
    success_rate = fields.Float(string='Taux de réussite', compute='_compute_metrics', digits=(5, 2))
    
    @api.depends('student_ids', 'course_ids', 'batch_ids', 'faculty_ids', 'period_ids', 'date_from', 'date_to')
    def _compute_metrics(self):
        """Calcule les métriques du tableau de bord"""
        for record in self:
            domain = [('state', 'in', ['confirmed', 'published'])]
            
            if record.student_ids:
                domain.append(('student_id', 'in', record.student_ids.ids))
            if record.course_ids:
                domain.append(('course_id', 'in', record.course_ids.ids))
            if record.batch_ids:
                domain.append(('batch_id', 'in', record.batch_ids.ids))
            if record.faculty_ids:
                domain.append(('faculty_id', 'in', record.faculty_ids.ids))
            if record.period_ids:
                domain.append(('period_id', 'in', record.period_ids.ids))
            if record.date_from:
                domain.append(('date', '>=', record.date_from))
            if record.date_to:
                domain.append(('date', '<=', record.date_to))
            
            evaluations = self.env['edu.evaluation'].search(domain)
            
            record.total_evaluations = len(evaluations)
            record.average_grade = sum(evaluations.mapped('grade_percentage')) / len(evaluations) if evaluations else 0
            
            passed = evaluations.filtered(lambda e: e.grade_percentage >= 50 and not e.is_absent)
            total_non_absent = evaluations.filtered(lambda e: not e.is_absent)
            record.success_rate = (len(passed) * 100.0 / len(total_non_absent)) if total_non_absent else 0
