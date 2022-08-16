# -*- coding: utf-8 -*-
{
    'name': 'Ohme-Helpdesk',
    'version': '1.0',
    'summary': 'Helpdesk customisations',
    'author': 'Dhruvil Goswami, Ohme-UK',
    'category': 'Services/Helpdesk',
    'website': 'https://github.com/dhruvil-ohme',
    'description': """
    This module will allow user to associate an Installer with a customer ticket.
    """,
    'depends': ['helpdesk'],
    'data': [
        'views/helpdesk_ticket_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: