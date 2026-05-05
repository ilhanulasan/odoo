# -*- coding: utf-8 -*-
{
    'name': 'Contacts Portal Contact Type',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Portal contact type on partners',
    'depends': ['contacts', 'portal', 'account', 'shuttle_management'],
    'assets': {
        'web.assets_backend': [
            'contacts_portal_type/static/src/widgets/partner_location_map/partner_location_map_widget.js',
            'contacts_portal_type/static/src/widgets/partner_location_map/partner_location_map_widget.xml',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/portal_templates.xml',
        'views/portal_role_pages.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
