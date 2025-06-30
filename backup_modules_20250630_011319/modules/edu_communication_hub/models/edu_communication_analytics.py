# -*- coding: utf-8 -*-

from odoo import models, fields, tools


class EduCommunicationAnalytics(models.Model):
    _name = 'edu.communication.analytics'
    _description = 'Analytics de communication'
    _auto = False
    
    message_id = fields.Many2one('edu.message', 'Message')
    date = fields.Date('Date')
    message_type = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push'),
        ('chat', 'Chat'),
    ], string='Type')
    
    recipient_count = fields.Integer('Nombre de destinataires')
    sent_count = fields.Integer('Envoyés')
    delivered_count = fields.Integer('Délivrés')
    opened_count = fields.Integer('Ouverts')
    clicked_count = fields.Integer('Cliqués')
    
    def init(self):
        """Initialiser la vue SQL"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    m.id as message_id,
                    m.create_date::date as date,
                    m.message_type,
                    1 as recipient_count,
                    CASE WHEN m.state IN ('sent', 'delivered', 'opened', 'clicked') THEN 1 ELSE 0 END as sent_count,
                    CASE WHEN m.state IN ('delivered', 'opened', 'clicked') THEN 1 ELSE 0 END as delivered_count,
                    CASE WHEN m.state IN ('opened', 'clicked') THEN 1 ELSE 0 END as opened_count,
                    CASE WHEN m.state = 'clicked' THEN 1 ELSE 0 END as clicked_count
                FROM edu_message m
            )
        """ % self._table)
