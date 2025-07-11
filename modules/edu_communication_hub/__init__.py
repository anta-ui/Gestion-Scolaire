# -*- coding: utf-8 -*-

from . import models
# from . import wizard
# from . import controllers

# Commenté temporairement pour simplifier l'installation
# def post_init_hook(env):
#     """Hook appelé après l'installation du module"""
#     import logging
#     _logger = logging.getLogger(__name__)
#     
#     try:
#         # Créer la configuration par défaut
#         config = env['edu.communication.config'].search([], limit=1)
#         if not config:
#             env['edu.communication.config'].create({
#                 'name': 'Configuration par défaut',
#                 'active': True,
#                 'default_sms_provider': 'twilio',
#                 'default_email_provider': 'sendgrid',
#                 'enable_push_notifications': True,
#                 'enable_chat': True,
#                 'auto_send_attendance_notifications': True,
#                 'auto_send_grade_notifications': True,
#             })
#         
#         # Créer les types de notifications par défaut
#         notification_types = [
#             ('absence', 'Notification d\'absence', 'high'),
#             ('grade', 'Nouvelle note', 'normal'),
#             ('announcement', 'Annonce générale', 'normal'),
#             ('event', 'Événement', 'normal'),
#             ('homework', 'Devoir à rendre', 'normal'),
#             ('meeting', 'Réunion parents', 'high'),
#         ]
#         
#         for code, name, priority in notification_types:
#             existing = env['edu.notification.type'].search([('code', '=', code)])
#             if not existing:
#                 env['edu.notification.type'].create({
#                     'name': name,
#                     'code': code,
#                     'priority': priority,
#                     'use_email': True,
#                     'active': True,
#                 })
#         
#         _logger.info("Module edu_communication_hub initialisé avec succès")
#         
#     except Exception as e:
#         _logger.error(f"Erreur lors de l'initialisation du module: {e}")
