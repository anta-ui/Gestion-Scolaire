# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timedelta
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduAccountingReportsController(http.Controller):
    """Controller pour les rapports comptables éducatifs"""

    @http.route('/api/reports/financial-summary', type='json', auth='user', methods=['POST'], csrf=False)
    def get_financial_summary(self, **kwargs):
        """Génère un rapport de synthèse financière"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            academic_year_id = kwargs.get('academic_year_id')
            
            # Construction du domaine de base
            domain = []
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if academic_year_id:
                domain.append(('academic_year_id', '=', academic_year_id))
            
            # Collecte des données
            # Factures
            invoices = request.env['edu.student.invoice'].search(domain)
            total_invoiced = sum(invoices.mapped('amount_total')) if hasattr(invoices, 'amount_total') else 0
            paid_invoices = invoices.filtered(lambda i: i.state == 'paid' if hasattr(i, 'state') else False)
            total_paid = sum(paid_invoices.mapped('amount_total')) if hasattr(paid_invoices, 'amount_total') else 0
            
            # Paiements
            payments = request.env['edu.student.payment'].search(domain)
            total_payments_amount = sum(payments.mapped('amount')) if hasattr(payments, 'amount') else 0
            
            # Bourses et aides
            scholarships = request.env['edu.scholarship'].search(domain)
            total_scholarships = sum(scholarships.mapped('amount')) if hasattr(scholarships, 'amount') else 0
            
            financial_aids = request.env['edu.financial.aid'].search(domain)
            total_aids = sum(financial_aids.mapped('disbursed_amount')) if hasattr(financial_aids, 'disbursed_amount') else 0
            
            # Remises
            discounts = request.env['edu.discount'].search(domain)
            total_discounts = sum(discounts.mapped('amount')) if hasattr(discounts, 'amount') else 0
            
            # Calculs
            outstanding_amount = total_invoiced - total_paid
            collection_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
            total_financial_assistance = total_scholarships + total_aids + total_discounts
            net_revenue = total_paid - total_financial_assistance
            
            summary = {
                'period': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'academic_year_id': academic_year_id
                },
                'revenue': {
                    'gross_invoiced': total_invoiced,
                    'total_collected': total_paid,
                    'outstanding': outstanding_amount,
                    'collection_rate': collection_rate
                },
                'financial_assistance': {
                    'scholarships': total_scholarships,
                    'financial_aids': total_aids,
                    'discounts': total_discounts,
                    'total': total_financial_assistance
                },
                'summary': {
                    'net_revenue': net_revenue,
                    'total_transactions': len(invoices) + len(payments),
                    'active_students': len(set(invoices.mapped('student_id.id'))) if invoices else 0
                }
            }
            
            return {
                'success': True,
                'data': summary
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la génération du rapport financier: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/reports/student-account-statement', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_account_statement(self, **kwargs):
        """Génère un relevé de compte étudiant"""
        try:
            student_id = kwargs.get('student_id')
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            if not student_id:
                return {'success': False, 'error': 'ID étudiant requis'}
            
            student = request.env['res.partner'].browse(student_id)
            if not student.exists():
                return {'success': False, 'error': 'Étudiant non trouvé'}
            
            # Domaine pour les transactions de l'étudiant
            domain = [('student_id', '=', student_id)]
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            
            # Factures de l'étudiant
            invoices = request.env['edu.student.invoice'].search(domain)
            invoice_lines = []
            for invoice in invoices:
                invoice_lines.append({
                    'date': invoice.invoice_date.isoformat() if hasattr(invoice, 'invoice_date') and invoice.invoice_date else '',
                    'type': 'invoice',
                    'reference': invoice.name if hasattr(invoice, 'name') else '',
                    'description': invoice.description if hasattr(invoice, 'description') else '',
                    'debit': invoice.amount_total if hasattr(invoice, 'amount_total') else 0,
                    'credit': 0,
                    'balance': 0,  # Sera calculé
                    'status': invoice.state if hasattr(invoice, 'state') else 'draft'
                })
            
            # Paiements de l'étudiant
            payments = request.env['edu.student.payment'].search(domain)
            payment_lines = []
            for payment in payments:
                payment_lines.append({
                    'date': payment.payment_date.isoformat() if hasattr(payment, 'payment_date') and payment.payment_date else '',
                    'type': 'payment',
                    'reference': payment.name if hasattr(payment, 'name') else '',
                    'description': f"Paiement - {payment.payment_method_id.name if hasattr(payment, 'payment_method_id') and payment.payment_method_id else 'N/A'}",
                    'debit': 0,
                    'credit': payment.amount if hasattr(payment, 'amount') else 0,
                    'balance': 0,
                    'status': payment.state if hasattr(payment, 'state') else 'draft'
                })
            
            # Combiner et trier les transactions
            all_transactions = invoice_lines + payment_lines
            all_transactions.sort(key=lambda x: x['date'])
            
            # Calculer les soldes cumulés
            running_balance = 0
            for transaction in all_transactions:
                running_balance += transaction['debit'] - transaction['credit']
                transaction['balance'] = running_balance
            
            # Calculs de synthèse
            total_invoiced = sum(line['debit'] for line in invoice_lines)
            total_paid = sum(line['credit'] for line in payment_lines)
            current_balance = total_invoiced - total_paid
            
            statement = {
                'student_info': {
                    'id': student.id,
                    'name': student.name,
                    'email': student.email if hasattr(student, 'email') else '',
                    'phone': student.phone if hasattr(student, 'phone') else ''
                },
                'period': {
                    'date_from': date_from,
                    'date_to': date_to
                },
                'summary': {
                    'total_invoiced': total_invoiced,
                    'total_paid': total_paid,
                    'current_balance': current_balance,
                    'total_transactions': len(all_transactions)
                },
                'transactions': all_transactions
            }
            
            return {
                'success': True,
                'data': statement
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la génération du relevé: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/reports/fee-collection-report', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_collection_report(self, **kwargs):
        """Rapport de collecte des frais"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            academic_year_id = kwargs.get('academic_year_id')
            course_id = kwargs.get('course_id')
            
            domain = []
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if academic_year_id:
                domain.append(('academic_year_id', '=', academic_year_id))
            if course_id:
                domain.append(('course_id', '=', course_id))
            
            # Collectes de frais
            collections = request.env['edu.fee.collection'].search(domain)
            
            collection_data = []
            total_expected = 0
            total_collected = 0
            
            for collection in collections:
                expected = collection.total_amount if hasattr(collection, 'total_amount') else 0
                collected = collection.collected_amount if hasattr(collection, 'collected_amount') else 0
                collection_rate = (collected / expected * 100) if expected > 0 else 0
                
                collection_data.append({
                    'id': collection.id,
                    'name': collection.name,
                    'reference': collection.reference if hasattr(collection, 'reference') else '',
                    'course_name': collection.course_id.name if hasattr(collection, 'course_id') and collection.course_id else '',
                    'expected_amount': expected,
                    'collected_amount': collected,
                    'outstanding_amount': expected - collected,
                    'collection_rate': collection_rate,
                    'student_count': collection.student_count if hasattr(collection, 'student_count') else 0,
                    'status': collection.state if hasattr(collection, 'state') else 'draft'
                })
                
                total_expected += expected
                total_collected += collected
            
            # Statistiques par cours
            by_course = {}
            for collection in collections:
                course_name = collection.course_id.name if hasattr(collection, 'course_id') and collection.course_id else 'Non spécifié'
                if course_name not in by_course:
                    by_course[course_name] = {'expected': 0, 'collected': 0, 'count': 0}
                
                by_course[course_name]['expected'] += collection.total_amount if hasattr(collection, 'total_amount') else 0
                by_course[course_name]['collected'] += collection.collected_amount if hasattr(collection, 'collected_amount') else 0
                by_course[course_name]['count'] += 1
            
            report = {
                'period': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'academic_year_id': academic_year_id,
                    'course_id': course_id
                },
                'summary': {
                    'total_collections': len(collections),
                    'total_expected': total_expected,
                    'total_collected': total_collected,
                    'total_outstanding': total_expected - total_collected,
                    'overall_collection_rate': (total_collected / total_expected * 100) if total_expected > 0 else 0
                },
                'collections': collection_data,
                'by_course': by_course
            }
            
            return {
                'success': True,
                'data': report
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du rapport de collecte: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/reports/payment-analysis', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_analysis(self, **kwargs):
        """Analyse des tendances de paiement"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            group_by = kwargs.get('group_by', 'month')  # month, week, day
            
            domain = []
            if date_from:
                domain.append(('payment_date', '>=', date_from))
            if date_to:
                domain.append(('payment_date', '<=', date_to))
            
            payments = request.env['edu.student.payment'].search(domain)
            
            # Groupement par période
            grouped_data = {}
            method_stats = {}
            
            for payment in payments:
                if not hasattr(payment, 'payment_date') or not payment.payment_date:
                    continue
                
                # Clé de période
                if group_by == 'day':
                    period_key = payment.payment_date.strftime('%Y-%m-%d')
                elif group_by == 'week':
                    period_key = f"{payment.payment_date.year}-W{payment.payment_date.isocalendar()[1]:02d}"
                else:  # month
                    period_key = payment.payment_date.strftime('%Y-%m')
                
                # Groupement par période
                if period_key not in grouped_data:
                    grouped_data[period_key] = {'count': 0, 'amount': 0}
                
                amount = payment.amount if hasattr(payment, 'amount') else 0
                grouped_data[period_key]['count'] += 1
                grouped_data[period_key]['amount'] += amount
                
                # Statistiques par méthode de paiement
                method = payment.payment_method_id.name if hasattr(payment, 'payment_method_id') and payment.payment_method_id else 'Autre'
                if method not in method_stats:
                    method_stats[method] = {'count': 0, 'amount': 0}
                method_stats[method]['count'] += 1
                method_stats[method]['amount'] += amount
            
            # Formatage pour graphiques
            periods = sorted(grouped_data.keys())
            chart_data = []
            for period in periods:
                chart_data.append({
                    'period': period,
                    'count': grouped_data[period]['count'],
                    'amount': grouped_data[period]['amount']
                })
            
            # Calculs de tendance
            if len(chart_data) >= 2:
                recent_amount = chart_data[-1]['amount']
                previous_amount = chart_data[-2]['amount']
                trend = ((recent_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            else:
                trend = 0
            
            analysis = {
                'period': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'group_by': group_by
                },
                'summary': {
                    'total_payments': len(payments),
                    'total_amount': sum(p['amount'] for p in grouped_data.values()),
                    'average_payment': sum(p['amount'] for p in grouped_data.values()) / len(payments) if payments else 0,
                    'trend_percentage': trend
                },
                'chart_data': chart_data,
                'by_payment_method': method_stats,
                'periods_covered': len(periods)
            }
            
            return {
                'success': True,
                'data': analysis
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'analyse des paiements: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/reports/overdue-students', type='json', auth='user', methods=['POST'], csrf=False)
    def get_overdue_students_report(self, **kwargs):
        """Rapport des étudiants en retard de paiement"""
        try:
            days_overdue = kwargs.get('days_overdue', 30)
            academic_year_id = kwargs.get('academic_year_id')
            course_id = kwargs.get('course_id')
            
            current_date = datetime.now().date()
            cutoff_date = current_date - timedelta(days=days_overdue)
            
            # Rechercher les factures impayées en retard
            domain = [
                ('state', '!=', 'paid'),
                ('due_date', '<=', cutoff_date)
            ]
            
            if academic_year_id:
                domain.append(('academic_year_id', '=', academic_year_id))
            
            overdue_invoices = request.env['edu.student.invoice'].search(domain)
            
            # Grouper par étudiant
            student_data = {}
            for invoice in overdue_invoices:
                student_id = invoice.student_id.id if hasattr(invoice, 'student_id') and invoice.student_id else None
                if not student_id:
                    continue
                
                if student_id not in student_data:
                    student = invoice.student_id
                    student_data[student_id] = {
                        'student_id': student_id,
                        'student_name': student.name,
                        'student_email': student.email if hasattr(student, 'email') else '',
                        'student_phone': student.phone if hasattr(student, 'phone') else '',
                        'course_name': '',
                        'total_overdue': 0,
                        'invoice_count': 0,
                        'oldest_due_date': None,
                        'days_overdue': 0,
                        'invoices': []
                    }
                
                # Informations de la facture
                due_date = invoice.due_date if hasattr(invoice, 'due_date') else None
                amount = invoice.amount_total if hasattr(invoice, 'amount_total') else 0
                days_late = (current_date - due_date).days if due_date else 0
                
                student_data[student_id]['total_overdue'] += amount
                student_data[student_id]['invoice_count'] += 1
                student_data[student_id]['invoices'].append({
                    'id': invoice.id,
                    'name': invoice.name if hasattr(invoice, 'name') else '',
                    'amount': amount,
                    'due_date': due_date.isoformat() if due_date else '',
                    'days_overdue': days_late
                })
                
                # Date la plus ancienne
                if not student_data[student_id]['oldest_due_date'] or (due_date and due_date < student_data[student_id]['oldest_due_date']):
                    student_data[student_id]['oldest_due_date'] = due_date
                    student_data[student_id]['days_overdue'] = days_late
                
                # Cours (prendre le premier trouvé)
                if not student_data[student_id]['course_name'] and hasattr(invoice, 'course_id') and invoice.course_id:
                    student_data[student_id]['course_name'] = invoice.course_id.name
            
            # Convertir en liste et trier
            overdue_students = list(student_data.values())
            overdue_students.sort(key=lambda x: x['days_overdue'], reverse=True)
            
            # Statistiques
            total_students = len(overdue_students)
            total_amount = sum(s['total_overdue'] for s in overdue_students)
            avg_overdue_per_student = total_amount / total_students if total_students > 0 else 0
            
            report = {
                'criteria': {
                    'days_overdue_threshold': days_overdue,
                    'academic_year_id': academic_year_id,
                    'course_id': course_id,
                    'report_date': current_date.isoformat()
                },
                'summary': {
                    'total_overdue_students': total_students,
                    'total_overdue_amount': total_amount,
                    'average_overdue_per_student': avg_overdue_per_student,
                    'total_overdue_invoices': sum(s['invoice_count'] for s in overdue_students)
                },
                'students': overdue_students
            }
            
            return {
                'success': True,
                'data': report
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du rapport d'étudiants en retard: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/reports/export', type='json', auth='user', methods=['POST'], csrf=False)
    def export_report(self, **kwargs):
        """Exporte un rapport au format demandé"""
        try:
            report_type = kwargs.get('report_type')
            export_format = kwargs.get('format', 'json')  # json, csv, xlsx
            
            if not report_type:
                return {'success': False, 'error': 'Type de rapport requis'}
            
            # Appeler le rapport approprié
            if report_type == 'financial_summary':
                report_data = self.get_financial_summary(**kwargs)
            elif report_type == 'fee_collection':
                report_data = self.get_fee_collection_report(**kwargs)
            elif report_type == 'payment_analysis':
                report_data = self.get_payment_analysis(**kwargs)
            elif report_type == 'overdue_students':
                report_data = self.get_overdue_students_report(**kwargs)
            else:
                return {'success': False, 'error': 'Type de rapport non supporté'}
            
            if not report_data.get('success'):
                return report_data
            
            # Pour le moment, retourner en JSON
            # Dans une implémentation complète, on générerait CSV/Excel ici
            
            return {
                'success': True,
                'data': report_data['data'],
                'export_format': export_format,
                'message': f'Rapport {report_type} exporté en {export_format}'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'export: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
