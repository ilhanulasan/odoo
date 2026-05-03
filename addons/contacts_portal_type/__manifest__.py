# -*- coding: utf-8 -*-
{
    'name': 'Contacts Portal Contact Type',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Portal contact type on partners',
    'depends': ['contacts', 'portal'],
    'data': [
        'views/res_partner_views.xml',
        'views/portal_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
