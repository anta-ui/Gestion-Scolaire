# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EduAccountingDashboard(models.Model):
    _name = 'edu.accounting.dashboard'
    _description = 'Tableau de Bord Comptable Éducatif'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du Tableau de Bord',
        required=True,
        default='Tableau de Bord Comptable'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company
    )

    @api.model
    def get_financial_summary(self):
        """Retourne un résumé financier pour le tableau de bord"""
        return {
            'total_invoices': 0,
            'total_payments': 0,
            'pending_payments': 0,
            'overdue_invoices': 0,
        } 