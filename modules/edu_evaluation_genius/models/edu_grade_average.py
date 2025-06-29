# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EduGradeAverage(models.Model):
    """Calcul et gestion des moyennes"""
    _name = 'edu.grade.average'
    _description = 'Moyenne des notes'
    _order = 'student_id, period_id, course_id'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True
    )
    
    # Relations principales
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        index=True
    )
    
    course_id = fields.Many2one(
        'op.course',
        string='Matière',
        index=True
    )
    
    batch_id = fields.Many2one(
        'op.batch',
        string='Groupe',
        required=True,
        index=True,
        help="Groupe/Classe de l'élève"
    )
    
    period_id = fields.Many2one(
        'edu.evaluation.period',
        string='Période',
        required=True,
        index=True
    )
    
    # Configuration
    average_type = fields.Selection([
        ('general', 'Moyenne générale'),
        ('course', 'Moyenne par matière'),
        ('competency', 'Moyenne par compétence'),
        ('period', 'Moyenne de période')
    ], string='Type de moyenne', required=True, default='course')
    
    competency_id = fields.Many2one(
        'edu.competency',
        string='Compétence',
        help="Compétence concernée (si applicable)"
    )
    
    # Calculs de moyenne
    total_points = fields.Float(
        string='Total des points',
        digits=(12, 2),
        compute='_compute_averages',
        store=True
    )
    
    total_max_points = fields.Float(
        string='Total points maximum',
        digits=(12, 2),
        compute='_compute_averages',
        store=True
    )
    
    total_coefficient = fields.Float(
        string='Total coefficient',
        digits=(8, 2),
        compute='_compute_averages',
        store=True
    )
    
    weighted_average = fields.Float(
        string='Moyenne pondérée',
        digits=(6, 2),
        compute='_compute_averages',
        store=True,
        help="Moyenne pondérée par les coefficients"
    )
    
    simple_average = fields.Float(
        string='Moyenne simple',
        digits=(6, 2),
        compute='_compute_averages',
        store=True,
        help="Moyenne arithmétique simple"
    )
    
    percentage = fields.Float(
        string='Pourcentage',
        digits=(5, 2),
        compute='_compute_averages',
        store=True
    )
    
    grade_letter = fields.Char(
        string='Note lettre',
        compute='_compute_grade_letter',
        store=True
    )
    
    # Statistiques
    evaluation_count = fields.Integer(
        string='Nombre d\'évaluations',
        compute='_compute_averages',
        store=True
    )
    
    min_grade = fields.Float(
        string='Note minimale',
        digits=(6, 2),
        compute='_compute_averages',
        store=True
    )
    
    max_grade = fields.Float(
        string='Note maximale',
        digits=(6, 2),
        compute='_compute_averages',
        store=True
    )
    
    # Métadonnées
    last_update = fields.Datetime(
        string='Dernière mise à jour',
        default=fields.Datetime.now,
        readonly=True
    )
    
    is_final = fields.Boolean(
        string='Moyenne finale',
        default=False,
        help="Cette moyenne est-elle définitive ?"
    )
    
    comment = fields.Text(
        string='Commentaire',
        help="Commentaire sur cette moyenne"
    )
    
    @api.depends('student_id', 'course_id', 'period_id', 'average_type', 'competency_id')
    def _compute_display_name(self):
        """Calcule le nom d'affichage"""
        for record in self:
            parts = []
            if record.student_id:
                parts.append(record.student_id.name)
            
            if record.average_type == 'general':
                parts.append('Moyenne générale')
            elif record.average_type == 'course' and record.course_id:
                parts.append(record.course_id.name)
            elif record.average_type == 'competency' and record.competency_id:
                parts.append(record.competency_id.name)
            
            if record.period_id:
                parts.append(f"({record.period_id.name})")
            
            record.display_name = ' - '.join(parts) if parts else 'Moyenne'
    
    @api.depends('student_id', 'course_id', 'period_id', 'average_type', 'competency_id')
    def _compute_averages(self):
        """Calcule les moyennes et statistiques"""
        for record in self:
            # Construction du domaine de recherche
            domain = [
                ('student_id', '=', record.student_id.id),
                ('period_id', '=', record.period_id.id),
                ('state', 'in', ['confirmed', 'published']),
                ('is_absent', '=', False)  # Exclure les absences
            ]
            
            if record.average_type == 'course' and record.course_id:
                domain.append(('course_id', '=', record.course_id.id))
            elif record.average_type == 'competency' and record.competency_id:
                # Rechercher les évaluations liées à cette compétence
                competency_evaluations = self.env['edu.competency.evaluation'].search([
                    ('competency_id', '=', record.competency_id.id),
                    ('student_id', '=', record.student_id.id)
                ])
                evaluation_ids = competency_evaluations.mapped('evaluation_id').ids
                if evaluation_ids:
                    domain.append(('id', 'in', evaluation_ids))
                else:
                    # Aucune évaluation trouvée
                    record.update({
                        'total_points': 0,
                        'total_max_points': 0,
                        'total_coefficient': 0,
                        'weighted_average': 0,
                        'simple_average': 0,
                        'percentage': 0,
                        'evaluation_count': 0,
                        'min_grade': 0,
                        'max_grade': 0,
                        'last_update': fields.Datetime.now()
                    })
                    continue
            
            evaluations = self.env['edu.evaluation'].search(domain)
            
            if not evaluations:
                record.update({
                    'total_points': 0,
                    'total_max_points': 0,
                    'total_coefficient': 0,
                    'weighted_average': 0,
                    'simple_average': 0,
                    'percentage': 0,
                    'evaluation_count': 0,
                    'min_grade': 0,
                    'max_grade': 0,
                    'last_update': fields.Datetime.now()
                })
                continue
            
            # Calculs
            total_points = sum(e.grade * e.coefficient for e in evaluations)
            total_max_points = sum(e.max_grade * e.coefficient for e in evaluations)
            total_coefficient = sum(e.coefficient for e in evaluations)
            
            weighted_avg = total_points / total_coefficient if total_coefficient > 0 else 0
            simple_avg = sum(e.grade for e in evaluations) / len(evaluations) if evaluations else 0
            percentage = (total_points / total_max_points * 100) if total_max_points > 0 else 0
            
            grades = evaluations.mapped('grade')
            min_grade = min(grades) if grades else 0
            max_grade = max(grades) if grades else 0
            
            record.update({
                'total_points': total_points,
                'total_max_points': total_max_points,
                'total_coefficient': total_coefficient,
                'weighted_average': weighted_avg,
                'simple_average': simple_avg,
                'percentage': percentage,
                'evaluation_count': len(evaluations),
                'min_grade': min_grade,
                'max_grade': max_grade,
                'last_update': fields.Datetime.now()
            })
    
    @api.depends('weighted_average', 'percentage')
    def _compute_grade_letter(self):
        """Calcule la note lettre basée sur le pourcentage"""
        for record in self:
            percentage = record.percentage
            if percentage >= 90:
                record.grade_letter = 'A+'
            elif percentage >= 85:
                record.grade_letter = 'A'
            elif percentage >= 80:
                record.grade_letter = 'A-'
            elif percentage >= 75:
                record.grade_letter = 'B+'
            elif percentage >= 70:
                record.grade_letter = 'B'
            elif percentage >= 65:
                record.grade_letter = 'B-'
            elif percentage >= 60:
                record.grade_letter = 'C+'
            elif percentage >= 55:
                record.grade_letter = 'C'
            elif percentage >= 50:
                record.grade_letter = 'C-'
            elif percentage >= 45:
                record.grade_letter = 'D+'
            elif percentage >= 40:
                record.grade_letter = 'D'
            else:
                record.grade_letter = 'F'
    
    @api.constrains('student_id', 'course_id', 'period_id', 'average_type', 'competency_id')
    def _check_unique_average(self):
        """Vérifie l'unicité de la moyenne"""
        for record in self:
            domain = [
                ('student_id', '=', record.student_id.id),
                ('period_id', '=', record.period_id.id),
                ('average_type', '=', record.average_type),
                ('id', '!=', record.id)
            ]
            
            if record.course_id:
                domain.append(('course_id', '=', record.course_id.id))
            else:
                domain.append(('course_id', '=', False))
                
            if record.competency_id:
                domain.append(('competency_id', '=', record.competency_id.id))
            else:
                domain.append(('competency_id', '=', False))
            
            if self.search_count(domain) > 0:
                raise ValidationError(_("Une moyenne de ce type existe déjà pour cet élève et cette période"))
    
    def action_recalculate(self):
        """Recalcule les moyennes"""
        self._compute_averages()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recalcul terminé'),
                'message': _('Les moyennes ont été recalculées'),
                'type': 'success'
            }
        }
    
    def action_set_final(self):
        """Marque la moyenne comme définitive"""
        self.ensure_one()
        self.is_final = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Moyenne finalisée'),
                'message': _('Cette moyenne est maintenant définitive'),
                'type': 'success'
            }
        }
    
    @api.model
    def calculate_all_averages(self, period_id=None):
        """Calcule toutes les moyennes pour une période donnée"""
        domain = []
        if period_id:
            domain.append(('period_id', '=', period_id))
        
        averages = self.search(domain)
        averages._compute_averages()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Calcul terminé'),
                'message': _('%d moyennes ont été recalculées') % len(averages),
                'type': 'success'
            }
        }


class EduGradeAverageWizard(models.TransientModel):
    """Assistant pour créer des moyennes en masse"""
    _name = 'edu.grade.average.wizard'
    _description = 'Assistant de création de moyennes'

    period_id = fields.Many2one(
        'edu.evaluation.period',
        string='Période',
        required=True
    )
    
    batch_ids = fields.Many2many(
        'op.batch',
        string='Groupes',
        help="Groupes pour lesquels créer les moyennes"
    )
    
    course_ids = fields.Many2many(
        'op.course',
        string='Matières'
    )
    
    average_type = fields.Selection([
        ('general', 'Moyenne générale'),
        ('course', 'Moyenne par matière'),
        ('competency', 'Moyenne par compétence')
    ], string='Type de moyenne', required=True, default='course')
    
    def action_create_averages(self):
        """Crée les moyennes en masse"""
        domain = []
        if self.batch_ids:
            domain.append(('batch_id', 'in', self.batch_ids.ids))
        
        students = self.env['op.student'].search(domain)
        created_count = 0
        
        for student in students:
            if self.average_type == 'general':
                # Une seule moyenne générale par élève/période
                existing = self.env['edu.grade.average'].search([
                    ('student_id', '=', student.id),
                    ('period_id', '=', self.period_id.id),
                    ('average_type', '=', 'general')
                ])
                if not existing:
                    self.env['edu.grade.average'].create({
                        'student_id': student.id,
                        'period_id': self.period_id.id,
                        'batch_id': student.batch_id.id,
                        'average_type': 'general'
                    })
                    created_count += 1
            
            elif self.average_type == 'course':
                # Une moyenne par matière
                courses = self.course_ids if self.course_ids else student.batch_id.course_ids
                for course in courses:
                    existing = self.env['edu.grade.average'].search([
                        ('student_id', '=', student.id),
                        ('period_id', '=', self.period_id.id),
                        ('course_id', '=', course.id),
                        ('average_type', '=', 'course')
                    ])
                    if not existing:
                        self.env['edu.grade.average'].create({
                            'student_id': student.id,
                            'period_id': self.period_id.id,
                            'batch_id': student.batch_id.id,
                            'course_id': course.id,
                            'average_type': 'course'
                        })
                        created_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Création terminée'),
                'message': _('%d moyennes ont été créées') % created_count,
                'type': 'success'
            }
        }
