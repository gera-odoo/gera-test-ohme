# -*- coding: utf-8 -*-
{
    'name': 'Aged Receivable Report with Invoice Date',
    'version': '1.0',
    'summary': 'Aged Receivable Report with Invoice Date',
    'author': 'Dhruvil Goswami, Ohme-UK',
    'category': 'Accounting/Accounting',
    'website': 'https://github.com/dhruvil-ohme',
    'description': """
Version: 1.0
    Aged Receivable Report will now take Invoice Date rather than Due date.
    Aged data from period table will also be fetched using Invoice Date.

Version: 1.1
    Report name changed to 'Aged Receivables by Invoice Date'
    Version 1.0 -> 1.1
    """,
    'depends': ['account_reports'],
    'data': [
        'data/account_financial_report_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: