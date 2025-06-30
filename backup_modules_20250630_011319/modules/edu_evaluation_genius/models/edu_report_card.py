# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EduReportCard(models.Model):
    """Bulletin de notes"""
    _name = 'edu.report.card'
    _description = 'Bulletin de notes'
    _order = 'student_id, period_id'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True
    )
    
    # Informations principales
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        tracking=True,
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
        tracking=True,
        index=True
    )
    
    academic_year = fields.Char(
        string='Année scolaire',
        compute='_compute_academic_year',
        store=True
    )
    
    # Configuration du bulletin
    template_id = fields.Many2one(
        'edu.report.card.template',
        string='Modèle de bulletin',
        help="Modèle utilisé pour ce bulletin"
    )
    
    report_type = fields.Selection([
        ('standard', 'Standard'),
        ('detailed', 'Détaillé'),
        ('competency', 'Par compétences'),
        ('summary', 'Résumé')
    ], string='Type de bulletin', default='standard', required=True)
    
    # Moyennes et notes
    general_average = fields.Float(
        string='Moyenne générale',
        digits=(6, 2),
        compute='_compute_averages',
        store=True
    )
    
    general_rank = fields.Integer(
        string='Rang général',
        compute='_compute_rank',
        store=True
    )
    
    class_size = fields.Integer(
        string='Effectif de la classe',
        compute='_compute_class_info',
        store=True
    )
    
    # Lignes de détail
    subject_line_ids = fields.One2many(
        'edu.report.card.subject.line',
        'report_card_id',
        string='Notes par matière'
    )
    
    competency_line_ids = fields.One2many(
        'edu.report.card.competency.line',
        'report_card_id',
        string='Évaluation des compétences'
    )
    
    # Commentaires et appréciations
    teacher_comment = fields.Text(
        string='Appréciation du professeur principal',
        tracking=True
    )
    
    director_comment = fields.Text(
        string='Appréciation du directeur',
        tracking=True
    )
    
    parent_comment = fields.Text(
        string='Observations des parents'
    )
    
    # Discipline et comportement
    behavior_grade = fields.Selection([
        ('excellent', 'Excellent'),
        ('very_good', 'Très bien'),
        ('good', 'Bien'),
        ('satisfactory', 'Satisfaisant'),
        ('needs_improvement', 'À améliorer')
    ], string='Comportement')
    
    attendance_rate = fields.Float(
        string='Taux de présence (%)',
        digits=(5, 2),
        compute='_compute_attendance',
        store=True
    )
    
    absence_days = fields.Integer(
        string='Jours d\'absence',
        compute='_compute_attendance',
        store=True
    )
    
    late_count = fields.Integer(
        string='Nombre de retards',
        compute='_compute_attendance',
        store=True
    )
    
    # État et workflow
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('published', 'Publié'),
        ('sent', 'Envoyé'),
        ('archived', 'Archivé')
    ], string='État', default='draft', tracking=True)
    
    # Métadonnées
    created_date = fields.Datetime(
        string='Date de création',
        default=fields.Datetime.now,
        readonly=True
    )
    
    validated_date = fields.Datetime(
        string='Date de validation',
        readonly=True
    )
    
    published_date = fields.Datetime(
        string='Date de publication',
        readonly=True
    )
    
    sent_date = fields.Datetime(
        string='Date d\'envoi',
        readonly=True
    )
    
    @api.depends('student_id', 'period_id')
    def _compute_display_name(self):
        """Calcule le nom d'affichage"""
        for record in self:
            if record.student_id and record.period_id:
                record.display_name = f"Bulletin - {record.student_id.name} - {record.period_id.name}"
            else:
                record.display_name = "Bulletin"
    
    @api.depends('period_id')
    def _compute_academic_year(self):
        """Calcule l'année scolaire"""
        for record in self:
            if record.period_id and record.period_id.academic_year:
                record.academic_year = record.period_id.academic_year
            else:
                record.academic_year = str(fields.Date.today().year)
    
    @api.depends('subject_line_ids.average')
    def _compute_averages(self):
        """Calcule la moyenne générale"""
        for record in self:
            if record.subject_line_ids:
                weighted_sum = sum(line.average * line.coefficient for line in record.subject_line_ids if line.average)
                total_coeff = sum(line.coefficient for line in record.subject_line_ids if line.average)
                record.general_average = weighted_sum / total_coeff if total_coeff > 0 else 0
            else:
                record.general_average = 0
    
    @api.depends('general_average', 'batch_id', 'period_id')
    def _compute_rank(self):
        """Calcule le rang dans la classe"""
        for record in self:
            if record.general_average and record.batch_id and record.period_id:
                # Rechercher tous les bulletins de la même classe et période
                same_class_reports = self.search([
                    ('batch_id', '=', record.batch_id.id),
                    ('period_id', '=', record.period_id.id),
                    ('state', 'in', ['validated', 'published', 'sent']),
                    ('id', '!=', record.id)
                ])
                
                # Compter combien ont une moyenne supérieure
                better_count = len([r for r in same_class_reports if r.general_average > record.general_average])
                record.general_rank = better_count + 1
            else:
                record.general_rank = 0
    
    @api.depends('batch_id', 'period_id')
    def _compute_class_info(self):
        """Calcule les informations de classe"""
        for record in self:
            if record.batch_id and record.period_id:
                # Compter les bulletins de la même classe et période
                record.class_size = self.search_count([
                    ('batch_id', '=', record.batch_id.id),
                    ('period_id', '=', record.period_id.id),
                    ('state', 'in', ['validated', 'published', 'sent'])
                ])
            else:
                record.class_size = 0
    
    @api.depends('student_id', 'period_id')
    def _compute_attendance(self):
        """Calcule les statistiques de présence"""
        for record in self:
            if record.student_id and record.period_id:
                # Rechercher les données d'assiduité (à adapter selon votre modèle)
                domain = [
                    ('student_id', '=', record.student_id.id),
                    ('date', '>=', record.period_id.start_date),
                    ('date', '<=', record.period_id.end_date)
                ]
                
                # Si vous avez un modèle d'assiduité
                # attendances = self.env['student.attendance'].search(domain)
                # record.absence_days = attendances.filtered(lambda a: a.state == 'absent').count()
                # record.late_count = attendances.filtered(lambda a: a.state == 'late').count()
                # total_days = attendances.count()
                # record.attendance_rate = ((total_days - record.absence_days) / total_days * 100) if total_days > 0 else 0
                
                # Valeurs par défaut en attendant
                record.absence_days = 0
                record.late_count = 0
                record.attendance_rate = 100.0
            else:
                record.absence_days = 0
                record.late_count = 0
                record.attendance_rate = 0
    
    @api.constrains('student_id', 'period_id')
    def _check_unique_report_card(self):
        """Vérifie l'unicité du bulletin par élève et période"""
        for record in self:
            existing = self.search([
                ('student_id', '=', record.student_id.id),
                ('period_id', '=', record.period_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_("Un bulletin existe déjà pour cet élève et cette période"))
    
    def action_generate_lines(self):
        """Génère automatiquement les lignes du bulletin"""
        self.ensure_one()
        
        # Supprimer les lignes existantes
        self.subject_line_ids.unlink()
        self.competency_line_ids.unlink()
        
        # Générer les lignes par matière
        averages = self.env['edu.grade.average'].search([
            ('student_id', '=', self.student_id.id),
            ('period_id', '=', self.period_id.id),
            ('average_type', '=', 'course')
        ])
        
        subject_lines = []
        for avg in averages:
            if avg.course_id:
                subject_lines.append((0, 0, {
                    'course_id': avg.course_id.id,
                    'average': avg.weighted_average,
                    'coefficient': avg.course_id.coefficient if hasattr(avg.course_id, 'coefficient') else 1.0,
                    'grade_letter': avg.grade_letter,
                    'evaluation_count': avg.evaluation_count
                }))
        
        self.subject_line_ids = subject_lines
        
        # Générer les lignes de compétences si nécessaire
        if self.report_type == 'competency':
            competency_averages = self.env['edu.grade.average'].search([
                ('student_id', '=', self.student_id.id),
                ('period_id', '=', self.period_id.id),
                ('average_type', '=', 'competency')
            ])
            
            competency_lines = []
            for comp_avg in competency_averages:
                if comp_avg.competency_id:
                    competency_lines.append((0, 0, {
                        'competency_id': comp_avg.competency_id.id,
                        'mastery_level': self._get_mastery_level(comp_avg.percentage),
                        'score': comp_avg.percentage,
                        'comment': f"Moyenne: {comp_avg.weighted_average:.2f}"
                    }))
            
            self.competency_line_ids = competency_lines
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Génération terminée'),
                'message': _('Les lignes du bulletin ont été générées'),
                'type': 'success'
            }
        }
    
    def _get_mastery_level(self, percentage):
        """Détermine le niveau de maîtrise basé sur le pourcentage"""
        if percentage >= 85:
            return 'expert'
        elif percentage >= 70:
            return 'advanced'
        elif percentage >= 55:
            return 'intermediate'
        elif percentage >= 40:
            return 'beginner'
        else:
            return 'insufficient'
    
    def action_validate(self):
        """Valide le bulletin"""
        self.ensure_one()
        self.state = 'validated'
        self.validated_date = fields.Datetime.now()
        
        # Générer les lignes si elles n'existent pas
        if not self.subject_line_ids:
            self.action_generate_lines()
    
    def action_publish(self):
        """Publie le bulletin"""
        self.ensure_one()
        if self.state != 'validated':
            raise ValidationError(_("Le bulletin doit être validé avant d'être publié"))
        
        self.state = 'published'
        self.published_date = fields.Datetime.now()
    
    def action_send(self):
        """Envoie le bulletin aux parents"""
        self.ensure_one()
        if self.state != 'published':
            raise ValidationError(_("Le bulletin doit être publié avant d'être envoyé"))
        
        self.state = 'sent'
        self.sent_date = fields.Datetime.now()
        
        # Ici vous pouvez ajouter la logique d'envoi par email
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulletin envoyé'),
                'message': _('Le bulletin a été envoyé aux parents'),
                'type': 'success'
            }
        }
    
    def action_print_report(self):
        """Imprime le bulletin"""
        self.ensure_one()
        return self.env.ref('edu_evaluation_genius.report_card_report').report_action(self)


class EduReportCardSubjectLine(models.Model):
    """Ligne de matière dans le bulletin"""
    _name = 'edu.report.card.subject.line'
    _description = 'Ligne matière du bulletin'
    _order = 'report_card_id, sequence, course_id'

    report_card_id = fields.Many2one(
        'edu.report.card',
        string='Bulletin',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(string='Séquence', default=10)
    
    course_id = fields.Many2one(
        'op.course',
        string='Matière',
        required=True
    )
    
    average = fields.Float(
        string='Moyenne',
        digits=(6, 2),
        required=True
    )
    
    coefficient = fields.Float(
        string='Coefficient',
        digits=(4, 2),
        default=1.0,
        required=True
    )
    
    grade_letter = fields.Char(
        string='Note lettre',
        size=3
    )
    
    evaluation_count = fields.Integer(
        string='Nb évaluations',
        default=0
    )
    
    teacher_comment = fields.Text(
        string='Appréciation du professeur'
    )
    
    rank_in_class = fields.Integer(
        string='Rang dans la classe'
    )


class EduReportCardCompetencyLine(models.Model):
    """Ligne de compétence dans le bulletin"""
    _name = 'edu.report.card.competency.line'
    _description = 'Ligne compétence du bulletin'
    _order = 'report_card_id, competency_id'

    report_card_id = fields.Many2one(
        'edu.report.card',
        string='Bulletin',
        required=True,
        ondelete='cascade'
    )
    
    competency_id = fields.Many2one(
        'edu.competency',
        string='Compétence',
        required=True
    )
    
    mastery_level = fields.Selection([
        ('insufficient', 'Insuffisant'),
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert')
    ], string='Niveau de maîtrise', required=True)
    
    score = fields.Float(
        string='Score',
        digits=(5, 2)
    )
    
    comment = fields.Text(
        string='Commentaire'
    )


class EduReportCardTemplate(models.Model):
    """Modèle de bulletin"""
    _name = 'edu.report.card.template'
    _description = 'Modèle de bulletin'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du modèle',
        required=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    report_type = fields.Selection([
        ('standard', 'Standard'),
        ('detailed', 'Détaillé'),
        ('competency', 'Par compétences'),
        ('summary', 'Résumé')
    ], string='Type de bulletin', default='standard', required=True)
    
    batch_ids = fields.Many2many(
        'op.batch',
        string='Groupes',
        help="Groupes pour lesquels ce modèle peut être utilisé"
    )
    
    include_behavior = fields.Boolean(
        string='Inclure le comportement',
        default=True
    )
    
    include_attendance = fields.Boolean(
        string='Inclure l\'assiduité',
        default=True
    )
    
    include_competencies = fields.Boolean(
        string='Inclure les compétences',
        default=False
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
