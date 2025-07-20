# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ParentAlertWizard(models.TransientModel):
    _name = 'parent.alert.wizard'
    _description = 'Assistant Alerte Parents'

    student_id = fields.Many2one('op.student', string='Élève', required=True)
    alert_type = fields.Selection([
        ('behavior', 'Comportement'),
        ('academic', 'Académique'),
        ('health', 'Santé'),
        ('absence', 'Absence'),
        ('other', 'Autre')
    ], string='Type d\'Alerte', required=True)
    
    urgency = fields.Selection([
        ('low', '🟢 Faible'),
        ('medium', '🟡 Moyenne'),
        ('high', '🔴 Haute')
    ], string='Urgence', required=True, default='medium')
    
    subject = fields.Char('Sujet', required=True)
    message = fields.Text('Message', required=True)
    
    send_sms = fields.Boolean('Envoyer SMS', default=True)
    send_email = fields.Boolean('Envoyer Email', default=True)
    
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        string='Pièces jointes'
    )

    @api.onchange('alert_type')
    def _onchange_alert_type(self):
        if self.alert_type:
            templates = {
                'behavior': 'Alerte Comportement: ',
                'academic': 'Suivi Académique: ',
                'health': 'Information Santé: ',
                'absence': 'Notification Absence: ',
                'other': 'Information: '
            }
            self.subject = templates.get(self.alert_type, '')

    def action_send_alert(self):
        self.ensure_one()
        if not self.student_id.family_group_id:
            raise UserError(_("L'élève n'a pas de groupe familial associé."))
            
        # Préparer le message
        values = {
            'subject': self.subject,
            'body': self.message,
            'partner_ids': [(4, parent.id) for parent in self.student_id.family_group_id.parent_ids],
            'attachment_ids': [(6, 0, self.attachment_ids.ids)],
        }
        
        # TODO: Créer l'enregistrement de communication (modèle à implémenter)
        # communication = self.env['student.communication'].create({
        #     'student_id': self.student_id.id,
        #     'type': 'alert',
        #     'subject': self.subject,
        #     'message': self.message,
        #     'urgency': self.urgency,
        #     'date': fields.Datetime.now(),
        # })
        
        # Envoyer email si activé
        if self.send_email:
            mail = self.env['mail.mail'].create(values)
            mail.send()
        
        # Envoyer SMS si activé et configuré
        if self.send_sms:
            self._send_sms_alert()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Succès'),
                'message': _('Alerte envoyée avec succès aux parents'),
                'type': 'success',
            }
        }

    def _send_sms_alert(self):
        """Envoie l'alerte par SMS"""
        if not self.student_id.family_group_id.parent_ids:
            return
            
        for parent in self.student_id.family_group_id.parent_ids:
            if parent.mobile:
                sms_template = f"{self.subject}\n{self.message[:160]}"  # Limite SMS
                # TODO: Implémenter l'envoi SMS si nécessaire
                # self.env['sms.api'].send_sms(parent.mobile, sms_template) 