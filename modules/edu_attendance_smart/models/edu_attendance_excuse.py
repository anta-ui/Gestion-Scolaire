# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduAttendanceExcuse(models.Model):
    """Justificatifs d'absence et de retard"""
    _name = 'edu.attendance.excuse'
    _description = 'Justificatif d\'absence/retard'
    _rec_name = 'name'
    _order = 'date desc'

    name = fields.Char('Motif', required=True)
    student_id = fields.Many2one('res.partner', 'Étudiant', required=True, 
                                domain="[('is_company', '=', False)]", ondelete='cascade')
    
    excuse_type = fields.Selection([
        ('absence', 'Absence'),
        ('late', 'Retard'),
        ('early_leave', 'Départ anticipé')
    ], string='Type', required=True, default='absence')
    
    date = fields.Date('Date', required=True, default=fields.Date.today)
    time_from = fields.Float('Heure de début', help="Heure de début de l'absence/retard")
    time_to = fields.Float('Heure de fin', help="Heure de fin de l'absence/retard")
    
    reason = fields.Selection([
        ('medical', 'Médical'),
        ('family', 'Familial'),
        ('transport', 'Transport'),
        ('personal', 'Personnel'),
        ('other', 'Autre')
    ], string='Raison', required=True)
    
    description = fields.Text('Description détaillée')
    
    # Documents justificatifs
    attachment_ids = fields.One2many('ir.attachment', 'res_id', 
                                   domain="[('res_model', '=', 'edu.attendance.excuse')]",
                                   string='Pièces jointes')
    
    # État du justificatif
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ], string='État', default='draft', required=True)
    
    # Validation
    approved_by = fields.Many2one('res.users', 'Approuvé par', readonly=True)
    approval_date = fields.Datetime('Date d\'approbation', readonly=True)
    rejection_reason = fields.Text('Motif de refus', readonly=True)
    
    # Liens avec les enregistrements de présence
    attendance_record_ids = fields.One2many('edu.attendance.record', 'excuse_id', 
                                          string='Enregistrements de présence')
    
    active = fields.Boolean('Actif', default=True)
    
    @api.constrains('time_from', 'time_to')
    def _check_times(self):
        """Vérifie que l'heure de fin est après l'heure de début"""
        for record in self:
            if record.time_from and record.time_to and record.time_from >= record.time_to:
                raise ValidationError(_("L'heure de fin doit être postérieure à l'heure de début."))
    
    @api.constrains('date')
    def _check_date(self):
        """Vérifie que la date n'est pas dans le futur"""
        for record in self:
            if record.date and record.date > fields.Date.today():
                raise ValidationError(_("La date du justificatif ne peut pas être dans le futur."))
    
    def action_submit(self):
        """Soumettre le justificatif pour approbation"""
        self.write({'state': 'submitted'})
    
    def action_approve(self):
        """Approuver le justificatif"""
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })
    
    def action_reject(self):
        """Rejeter le justificatif"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Motif de refus',
            'res_model': 'edu.attendance.excuse.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_excuse_id': self.id}
        }
    
    def action_reset_to_draft(self):
        """Remettre en brouillon"""
        self.write({
            'state': 'draft',
            'approved_by': False,
            'approval_date': False,
            'rejection_reason': False
        })
    
    @api.model
    def create(self, vals):
        """Création avec numérotation automatique"""
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('edu.attendance.excuse') or 'New'
        return super().create(vals)
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"{record.student_id.name} - {record.date} - {dict(record._fields['excuse_type'].selection)[record.excuse_type]}"
            result.append((record.id, name))
        return result 