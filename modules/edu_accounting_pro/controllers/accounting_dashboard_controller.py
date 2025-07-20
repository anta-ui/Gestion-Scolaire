# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timedelta
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduAccountingDashboardController(http.Controller):
    """Controller pour le tableau de bord comptable éducatif"""

    @http.route('/api/accounting-dashboard/overview', type='json', auth='user', methods=['POST'], csrf=False)
    def get_dashboard_overview(self, **kwargs):
        """Récupère un aperçu général du tableau de bord comptable"""
        try:
            # Filtres de période
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            academic_year_id = kwargs.get('academic_year_id')
            
            # Si pas de dates spécifiées, utiliser l'année en cours
            if not date_from and not date_to and not academic_year_id:
                current_date = datetime.now()
                date_from = current_date.replace(month=1, day=1).strftime('%Y-%m-%d')
                date_to = current_date.replace(month=12, day=31).strftime('%Y-%m-%d')
            
            domain_date = []
            if date_from:
                domain_date.append(('create_date', '>=', date_from))
            if date_to:
                domain_date.append(('create_date', '<=', date_to))
            if academic_year_id:
                domain_date.append(('academic_year_id', '=', academic_year_id))
            
            # Statistiques des factures étudiantes
            invoice_domain = domain_date.copy()
            invoices = request.env['edu.student.invoice'].search(invoice_domain)
            
            total_invoices = len(invoices)
            paid_invoices = len(invoices.filtered(lambda i: i.state == 'paid' if hasattr(i, 'state') else False))
            draft_invoices = len(invoices.filtered(lambda i: i.state == 'draft' if hasattr(i, 'state') else False))
            overdue_invoices = len(invoices.filtered(lambda i: 
                hasattr(i, 'due_date') and hasattr(i, 'state') and 
                i.due_date and i.due_date < datetime.now().date() and i.state != 'paid'
            ))
            
            total_invoice_amount = sum(invoices.mapped('amount_total')) if hasattr(invoices, 'amount_total') else 0
            paid_amount = sum(invoices.filtered(lambda i: i.state == 'paid' if hasattr(i, 'state') else False).mapped('amount_total')) if hasattr(invoices, 'amount_total') else 0
            outstanding_amount = total_invoice_amount - paid_amount
            
            # Statistiques des paiements
            payment_domain = domain_date.copy()
            payments = request.env['edu.student.payment'].search(payment_domain)
            
            total_payments = len(payments)
            validated_payments = len(payments.filtered(lambda p: p.state == 'validated' if hasattr(p, 'state') else False))
            total_payment_amount = sum(payments.mapped('amount')) if hasattr(payments, 'amount') else 0
            
            # Statistiques des bourses
            scholarship_domain = domain_date.copy()
            scholarships = request.env['edu.scholarship'].search(scholarship_domain)
            
            active_scholarships = len(scholarships.filtered(lambda s: s.state == 'active' if hasattr(s, 'state') else True))
            total_scholarship_amount = sum(scholarships.mapped('amount')) if hasattr(scholarships, 'amount') else 0
            
            # Statistiques des remises
            discount_domain = domain_date.copy()
            discounts = request.env['edu.discount'].search(discount_domain)
            
            active_discounts = len(discounts.filtered(lambda d: d.state == 'active' if hasattr(d, 'state') else True))
            total_discount_amount = sum(discounts.mapped('amount')) if hasattr(discounts, 'amount') else 0
            
            # Calculs de ratios
            payment_rate = (paid_amount / total_invoice_amount * 100) if total_invoice_amount > 0 else 0
            collection_efficiency = (validated_payments / total_payments * 100) if total_payments > 0 else 0
            
            data = {
                'period': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'academic_year_id': academic_year_id
                },
                'invoices': {
                    'total': total_invoices,
                    'paid': paid_invoices,
                    'draft': draft_invoices,
                    'overdue': overdue_invoices,
                    'total_amount': total_invoice_amount,
                    'paid_amount': paid_amount,
                    'outstanding_amount': outstanding_amount,
                    'payment_rate': payment_rate
                },
                'payments': {
                    'total': total_payments,
                    'validated': validated_payments,
                    'total_amount': total_payment_amount,
                    'collection_efficiency': collection_efficiency
                },
                'scholarships': {
                    'active': active_scholarships,
                    'total_amount': total_scholarship_amount
                },
                'discounts': {
                    'active': active_discounts,
                    'total_amount': total_discount_amount
                },
                'summary': {
                    'gross_revenue': total_invoice_amount,
                    'net_revenue': paid_amount,
                    'financial_aid': total_scholarship_amount + total_discount_amount,
                    'receivables': outstanding_amount
                }
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'aperçu: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-dashboard/revenue-trend', type='json', auth='user', methods=['POST'], csrf=False)
    def get_revenue_trend(self, **kwargs):
        """Récupère les tendances de revenus par période"""
        try:
            period_type = kwargs.get('period_type', 'month')  # month, week, day
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            # Définir la période par défaut (6 derniers mois)
            if not date_from or not date_to:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=180)
                date_from = start_date.strftime('%Y-%m-%d')
                date_to = end_date.strftime('%Y-%m-%d')
            
            # Récupérer les factures et paiements
            domain = [
                ('create_date', '>=', date_from),
                ('create_date', '<=', date_to)
            ]
            
            invoices = request.env['edu.student.invoice'].search(domain)
            payments = request.env['edu.student.payment'].search(domain)
            
            # Grouper par période
            revenue_data = {}
            payment_data = {}
            
            for invoice in invoices:
                period_key = self._get_period_key(invoice.create_date, period_type)
                if period_key not in revenue_data:
                    revenue_data[period_key] = 0
                revenue_data[period_key] += invoice.amount_total if hasattr(invoice, 'amount_total') else 0
            
            for payment in payments:
                period_key = self._get_period_key(payment.create_date, period_type)
                if period_key not in payment_data:
                    payment_data[period_key] = 0
                payment_data[period_key] += payment.amount if hasattr(payment, 'amount') else 0
            
            # Préparer les données pour le graphique
            all_periods = sorted(set(list(revenue_data.keys()) + list(payment_data.keys())))
            
            chart_data = []
            for period in all_periods:
                chart_data.append({
                    'period': period,
                    'invoiced': revenue_data.get(period, 0),
                    'collected': payment_data.get(period, 0)
                })
            
            return {
                'success': True,
                'data': {
                    'period_type': period_type,
                    'date_from': date_from,
                    'date_to': date_to,
                    'chart_data': chart_data,
                    'total_invoiced': sum(revenue_data.values()),
                    'total_collected': sum(payment_data.values())
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des tendances: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-dashboard/payment-methods', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_methods_statistics(self, **kwargs):
        """Récupère les statistiques par méthode de paiement"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            domain = []
            if date_from:
                domain.append(('payment_date', '>=', date_from))
            if date_to:
                domain.append(('payment_date', '<=', date_to))
            
            payments = request.env['edu.student.payment'].search(domain)
            
            method_stats = {}
            total_amount = 0
            
            for payment in payments:
                method = payment.payment_method_id.name if hasattr(payment, 'payment_method_id') and payment.payment_method_id else 'Non spécifié'
                amount = payment.amount if hasattr(payment, 'amount') else 0
                
                if method not in method_stats:
                    method_stats[method] = {'count': 0, 'amount': 0}
                
                method_stats[method]['count'] += 1
                method_stats[method]['amount'] += amount
                total_amount += amount
            
            # Calculer les pourcentages
            chart_data = []
            for method, stats in method_stats.items():
                percentage = (stats['amount'] / total_amount * 100) if total_amount > 0 else 0
                chart_data.append({
                    'method': method,
                    'count': stats['count'],
                    'amount': stats['amount'],
                    'percentage': percentage
                })
            
            # Trier par montant décroissant
            chart_data.sort(key=lambda x: x['amount'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'chart_data': chart_data,
                    'total_payments': len(payments),
                    'total_amount': total_amount,
                    'unique_methods': len(method_stats)
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors des statistiques de paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-dashboard/overdue-analysis', type='json', auth='user', methods=['POST'], csrf=False)
    def get_overdue_analysis(self, **kwargs):
        """Analyse des factures en retard"""
        try:
            current_date = datetime.now().date()
            
            # Récupérer les factures impayées
            unpaid_invoices = request.env['edu.student.invoice'].search([
                ('state', '!=', 'paid'),
                ('due_date', '!=', False)
            ])
            
            overdue_ranges = {
                '0-30': {'count': 0, 'amount': 0},
                '31-60': {'count': 0, 'amount': 0},
                '61-90': {'count': 0, 'amount': 0},
                '90+': {'count': 0, 'amount': 0}
            }
            
            total_overdue_amount = 0
            overdue_invoices = []
            
            for invoice in unpaid_invoices:
                if not hasattr(invoice, 'due_date') or not invoice.due_date:
                    continue
                    
                days_overdue = (current_date - invoice.due_date).days
                
                if days_overdue > 0:  # Facture en retard
                    invoice_data = {
                        'id': invoice.id,
                        'name': invoice.name if hasattr(invoice, 'name') else '',
                        'student_name': invoice.student_id.name if hasattr(invoice, 'student_id') and invoice.student_id else '',
                        'amount': invoice.amount_total if hasattr(invoice, 'amount_total') else 0,
                        'due_date': invoice.due_date.isoformat(),
                        'days_overdue': days_overdue
                    }
                    
                    overdue_invoices.append(invoice_data)
                    amount = invoice.amount_total if hasattr(invoice, 'amount_total') else 0
                    total_overdue_amount += amount
                    
                    # Classer par tranche de retard
                    if days_overdue <= 30:
                        overdue_ranges['0-30']['count'] += 1
                        overdue_ranges['0-30']['amount'] += amount
                    elif days_overdue <= 60:
                        overdue_ranges['31-60']['count'] += 1
                        overdue_ranges['31-60']['amount'] += amount
                    elif days_overdue <= 90:
                        overdue_ranges['61-90']['count'] += 1
                        overdue_ranges['61-90']['amount'] += amount
                    else:
                        overdue_ranges['90+']['count'] += 1
                        overdue_ranges['90+']['amount'] += amount
            
            # Trier les factures par nombre de jours de retard
            overdue_invoices.sort(key=lambda x: x['days_overdue'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'total_overdue_count': len(overdue_invoices),
                    'total_overdue_amount': total_overdue_amount,
                    'overdue_ranges': overdue_ranges,
                    'top_overdue_invoices': overdue_invoices[:10],  # Top 10 les plus en retard
                    'average_days_overdue': sum(inv['days_overdue'] for inv in overdue_invoices) / len(overdue_invoices) if overdue_invoices else 0
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'analyse des retards: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-dashboard/student-ranking', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_ranking(self, **kwargs):
        """Classement des étudiants par montant de paiements"""
        try:
            limit = kwargs.get('limit', 20)
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            ranking_type = kwargs.get('ranking_type', 'payments')  # payments, invoices, outstanding
            
            domain = []
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            
            if ranking_type == 'payments':
                # Classement par paiements
                payments = request.env['edu.student.payment'].search(domain)
                student_data = {}
                
                for payment in payments:
                    student_id = payment.student_id.id if hasattr(payment, 'student_id') and payment.student_id else None
                    if not student_id:
                        continue
                    
                    student_name = payment.student_id.name
                    amount = payment.amount if hasattr(payment, 'amount') else 0
                    
                    if student_id not in student_data:
                        student_data[student_id] = {
                            'name': student_name,
                            'total_amount': 0,
                            'count': 0
                        }
                    
                    student_data[student_id]['total_amount'] += amount
                    student_data[student_id]['count'] += 1
                
            elif ranking_type == 'invoices':
                # Classement par factures
                invoices = request.env['edu.student.invoice'].search(domain)
                student_data = {}
                
                for invoice in invoices:
                    student_id = invoice.student_id.id if hasattr(invoice, 'student_id') and invoice.student_id else None
                    if not student_id:
                        continue
                    
                    student_name = invoice.student_id.name
                    amount = invoice.amount_total if hasattr(invoice, 'amount_total') else 0
                    
                    if student_id not in student_data:
                        student_data[student_id] = {
                            'name': student_name,
                            'total_amount': 0,
                            'count': 0
                        }
                    
                    student_data[student_id]['total_amount'] += amount
                    student_data[student_id]['count'] += 1
            
            # Convertir en liste et trier
            ranking_list = []
            for student_id, data in student_data.items():
                ranking_list.append({
                    'student_id': student_id,
                    'student_name': data['name'],
                    'total_amount': data['total_amount'],
                    'count': data['count'],
                    'average_amount': data['total_amount'] / data['count'] if data['count'] > 0 else 0
                })
            
            # Trier par montant total décroissant
            ranking_list.sort(key=lambda x: x['total_amount'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'ranking_type': ranking_type,
                    'total_students': len(ranking_list),
                    'top_students': ranking_list[:limit],
                    'total_amount': sum(item['total_amount'] for item in ranking_list),
                    'average_per_student': sum(item['total_amount'] for item in ranking_list) / len(ranking_list) if ranking_list else 0
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du classement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-dashboard/kpis', type='json', auth='user', methods=['POST'], csrf=False)
    def get_key_performance_indicators(self, **kwargs):
        """Récupère les indicateurs clés de performance"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            # Domaine de base
            domain = []
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            
            # KPI Factures
            invoices = request.env['edu.student.invoice'].search(domain)
            total_invoices = len(invoices)
            paid_invoices = len(invoices.filtered(lambda i: i.state == 'paid' if hasattr(i, 'state') else False))
            
            # KPI Paiements
            payments = request.env['edu.student.payment'].search(domain)
            total_payments = len(payments)
            
            # KPI Temps de paiement moyen
            paid_invoice_days = []
            for invoice in invoices.filtered(lambda i: i.state == 'paid' if hasattr(i, 'state') else False):
                if hasattr(invoice, 'invoice_date') and hasattr(invoice, 'payment_date'):
                    if invoice.invoice_date and invoice.payment_date:
                        days = (invoice.payment_date - invoice.invoice_date).days
                        paid_invoice_days.append(days)
            
            avg_payment_days = sum(paid_invoice_days) / len(paid_invoice_days) if paid_invoice_days else 0
            
            # KPI Taux de recouvrement
            total_invoiced = sum(invoices.mapped('amount_total')) if hasattr(invoices, 'amount_total') else 0
            total_collected = sum(payments.mapped('amount')) if hasattr(payments, 'amount') else 0
            collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0
            
            # KPI Croissance (comparaison avec période précédente)
            previous_period_domain = []
            if date_from and date_to:
                period_duration = (datetime.strptime(date_to, '%Y-%m-%d') - datetime.strptime(date_from, '%Y-%m-%d')).days
                prev_end = datetime.strptime(date_from, '%Y-%m-%d') - timedelta(days=1)
                prev_start = prev_end - timedelta(days=period_duration)
                
                previous_period_domain = [
                    ('create_date', '>=', prev_start.strftime('%Y-%m-%d')),
                    ('create_date', '<=', prev_end.strftime('%Y-%m-%d'))
                ]
            
            prev_invoices = request.env['edu.student.invoice'].search(previous_period_domain)
            prev_total_invoiced = sum(prev_invoices.mapped('amount_total')) if hasattr(prev_invoices, 'amount_total') else 0
            
            revenue_growth = ((total_invoiced - prev_total_invoiced) / prev_total_invoiced * 100) if prev_total_invoiced > 0 else 0
            
            kpis = {
                'invoice_generation_rate': {
                    'value': total_invoices,
                    'label': 'Factures générées',
                    'type': 'number'
                },
                'payment_success_rate': {
                    'value': (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0,
                    'label': 'Taux de paiement (%)',
                    'type': 'percentage'
                },
                'collection_rate': {
                    'value': collection_rate,
                    'label': 'Taux de recouvrement (%)',
                    'type': 'percentage'
                },
                'average_payment_time': {
                    'value': avg_payment_days,
                    'label': 'Délai moyen de paiement (jours)',
                    'type': 'number'
                },
                'revenue_growth': {
                    'value': revenue_growth,
                    'label': 'Croissance du chiffre d\'affaires (%)',
                    'type': 'percentage'
                },
                'total_revenue': {
                    'value': total_invoiced,
                    'label': 'Chiffre d\'affaires total',
                    'type': 'currency'
                },
                'outstanding_amount': {
                    'value': total_invoiced - total_collected,
                    'label': 'Montant en attente',
                    'type': 'currency'
                }
            }
            
            return {
                'success': True,
                'data': kpis
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des KPIs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_period_key(self, date, period_type):
        """Génère une clé de période selon le type"""
        if period_type == 'day':
            return date.strftime('%Y-%m-%d')
        elif period_type == 'week':
            return f"{date.year}-W{date.isocalendar()[1]:02d}"
        elif period_type == 'month':
            return date.strftime('%Y-%m')
        elif period_type == 'year':
            return date.strftime('%Y')
        else:
            return date.strftime('%Y-%m')
