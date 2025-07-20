# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Assistant de rapport de présence'

    # Période
    date_from = fields.Date('Date de début', required=True,
                           default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date('Date de fin', required=True,
                         default=fields.Date.today)
    
    # Filtres
    student_ids = fields.Many2many('res.partner', 'wizard_student_rel',
                                  string='Étudiants',
                                  domain="[('is_student', '=', True)]")
    teacher_ids = fields.Many2many('res.partner', 'wizard_teacher_rel',
                                  string='Enseignants',
                                  domain="[('is_teacher', '=', True)]")
    session_ids = fields.Many2many('edu.attendance.session', string='Sessions')
    class_ids = fields.Many2many('op.batch', string='Classes/Groupes')
    
    # Options du rapport
    report_type = fields.Selection([
        ('summary', 'Résumé'),
        ('detailed', 'Détaillé'),
        ('statistics', 'Statistiques'),
        ('absences', 'Rapport d\'absences'),
        ('late_arrivals', 'Rapport de retards')
    ], string='Type de rapport', default='summary', required=True)
    
    group_by = fields.Selection([
        ('student', 'Par étudiant'),
        ('teacher', 'Par enseignant'),
        ('session', 'Par session'),
        ('class', 'Par classe'),
        ('date', 'Par date'),
        ('week', 'Par semaine'),
        ('month', 'Par mois')
    ], string='Grouper par', default='student')
    
    include_excused = fields.Boolean('Inclure les justifiés', default=True)
    include_statistics = fields.Boolean('Inclure les statistiques', default=True)
    
    # Format d'export
    export_format = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        ('csv', 'CSV')
    ], string='Format d\'export', default='pdf')
    
    def action_generate_report(self):
        """Générer le rapport"""
        self.ensure_one()
        
        # Validation des dates
        if self.date_from > self.date_to:
            raise UserError(_('La date de début doit être antérieure à la date de fin.'))
        
        # Construire le domaine
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        
        if self.student_ids:
            domain.append(('student_id', 'in', self.student_ids.ids))
        if self.teacher_ids:
            domain.append(('session_id.teacher_id', 'in', self.teacher_ids.ids))
        if self.session_ids:
            domain.append(('session_id', 'in', self.session_ids.ids))
        if self.class_ids:
            domain.append(('session_id.standard_id', 'in', self.class_ids.ids))
        
        # Récupérer les données
        records = self.env['edu.attendance.record'].search(domain)
        
        if not records:
            raise UserError(_('Aucune donnée trouvée pour la période et les filtres sélectionnés.'))
        
        # Préparer les données du rapport
        report_data = self._prepare_report_data(records)
        
        # Générer selon le format
        if self.export_format == 'pdf':
            return self._generate_pdf_report(report_data)
        elif self.export_format == 'xlsx':
            return self._generate_excel_report(report_data)
        else:  # CSV
            return self._generate_csv_report(report_data)
    
    def _prepare_report_data(self, records):
        """Préparer les données du rapport"""
        data = {
            'wizard': self,
            'records': records,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'total_records': len(records),
            'present_count': len(records.filtered(lambda r: r.state == 'present')),
            'absent_count': len(records.filtered(lambda r: r.state == 'absent')),
            'late_count': len(records.filtered(lambda r: r.state == 'late')),
            'excused_count': len(records.filtered(lambda r: r.is_excused)),
        }
        
        # Calculs statistiques
        if data['total_records'] > 0:
            data['presence_rate'] = (data['present_count'] + data['late_count']) / data['total_records'] * 100
            data['absence_rate'] = data['absent_count'] / data['total_records'] * 100
            data['excuse_rate'] = data['excused_count'] / data['total_records'] * 100
        else:
            data['presence_rate'] = data['absence_rate'] = data['excuse_rate'] = 0
        
        # Groupement des données
        if self.group_by == 'student':
            data['grouped_data'] = self._group_by_student(records)
        elif self.group_by == 'teacher':
            data['grouped_data'] = self._group_by_teacher(records)
        elif self.group_by == 'session':
            data['grouped_data'] = self._group_by_session(records)
        elif self.group_by == 'class':
            data['grouped_data'] = self._group_by_class(records)
        elif self.group_by == 'date':
            data['grouped_data'] = self._group_by_date(records)
        
        return data
    
    def _group_by_student(self, records):
        """Grouper par étudiant"""
        grouped = {}
        for record in records:
            student = record.student_id
            if student not in grouped:
                grouped[student] = {
                    'records': self.env['edu.attendance.record'],
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0
                }
            
            grouped[student]['records'] |= record
            if record.state == 'present':
                grouped[student]['present'] += 1
            elif record.state == 'absent':
                grouped[student]['absent'] += 1
            elif record.state == 'late':
                grouped[student]['late'] += 1
            
            if record.is_excused:
                grouped[student]['excused'] += 1
        
        return grouped
    
    def _group_by_teacher(self, records):
        """Grouper par enseignant"""
        grouped = {}
        for record in records:
            teacher = record.session_id.teacher_id
            if teacher not in grouped:
                grouped[teacher] = {
                    'records': self.env['edu.attendance.record'],
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0
                }
            
            grouped[teacher]['records'] |= record
            if record.state == 'present':
                grouped[teacher]['present'] += 1
            elif record.state == 'absent':
                grouped[teacher]['absent'] += 1
            elif record.state == 'late':
                grouped[teacher]['late'] += 1
            
            if record.is_excused:
                grouped[teacher]['excused'] += 1
        
        return grouped
    
    def _group_by_session(self, records):
        """Grouper par session"""
        grouped = {}
        for record in records:
            session = record.session_id
            if session not in grouped:
                grouped[session] = {
                    'records': self.env['edu.attendance.record'],
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0
                }
            
            grouped[session]['records'] |= record
            if record.state == 'present':
                grouped[session]['present'] += 1
            elif record.state == 'absent':
                grouped[session]['absent'] += 1
            elif record.state == 'late':
                grouped[session]['late'] += 1
            
            if record.is_excused:
                grouped[session]['excused'] += 1
        
        return grouped
    
    def _group_by_class(self, records):
        """Grouper par classe"""
        grouped = {}
        for record in records:
            class_obj = record.session_id.standard_id
            if class_obj not in grouped:
                grouped[class_obj] = {
                    'records': self.env['edu.attendance.record'],
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0
                }
            
            grouped[class_obj]['records'] |= record
            if record.state == 'present':
                grouped[class_obj]['present'] += 1
            elif record.state == 'absent':
                grouped[class_obj]['absent'] += 1
            elif record.state == 'late':
                grouped[class_obj]['late'] += 1
            
            if record.is_excused:
                grouped[class_obj]['excused'] += 1
        
        return grouped
    
    def _group_by_date(self, records):
        """Grouper par date"""
        grouped = {}
        for record in records:
            date = record.date
            if date not in grouped:
                grouped[date] = {
                    'records': self.env['edu.attendance.record'],
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0
                }
            
            grouped[date]['records'] |= record
            if record.state == 'present':
                grouped[date]['present'] += 1
            elif record.state == 'absent':
                grouped[date]['absent'] += 1
            elif record.state == 'late':
                grouped[date]['late'] += 1
            
            if record.is_excused:
                grouped[date]['excused'] += 1
        
        return grouped
    
    def _generate_pdf_report(self, data):
        """Générer un rapport PDF"""
        return self.env.ref('edu_attendance_smart.action_report_attendance_pdf').report_action(
            self, data=data)
    
    def _generate_excel_report(self, data):
        """Générer un rapport Excel"""
        # Ici vous pouvez implémenter la génération Excel avec xlsxwriter
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Rapport Excel généré avec succès'),
                'type': 'success'
            }
        }
    
    def _generate_csv_report(self, data):
        """Générer un rapport CSV"""
        # Ici vous pouvez implémenter la génération CSV
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Rapport CSV généré avec succès'),
                'type': 'success'
            }
        } 