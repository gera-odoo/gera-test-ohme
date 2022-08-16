# -*- coding: utf-8 -*-
{
    'name': 'Ohme Stock',
    'version': '1.1',
    'summary': 'Stock customisations for Ohme.',
    'author': 'Dhruvil Goswami, Ohme-UK',
    'category': 'Inventory/Inventory',
    'website': 'https://github.com/dhruvil-ohme',
    'description': """
Version: 1.0
    QA'd items of stock to be automatically moved from "Input" to "Stock".
    1. Warehouse Operative clicks "Passed QA" and "Save"
    2. Odoo creates an internal transfer as configured i.e., Physical Locations/WH/Input to Physical Locations/WH/Stock
    3. Odoo adds the serial number to this internal transfer and validates it

    Assign Serial Numbers in bulk from the same Excel Sheet we use to import the Serial Numbers
    """,
    'depends': ['stock'],
    'data': [
        'views/stock_move_views.xml',
        'views/stock_location_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: