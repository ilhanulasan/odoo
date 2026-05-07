# -*- coding: utf-8 -*-
{
    'name': 'Contacts Portal Contact Type',
    'version': '19.0.1.0.6',
    'category': 'Sales/CRM',
    'summary': 'Portal contact type on partners',
    'depends': [
        'contacts',
        'portal',
        'website',
        'sale',
        'account',
        'shuttle_management',
    ],
    'assets': {
        'web.assets_backend': [
            'contacts_portal_type/static/src/widgets/partner_location_map/partner_location_map_widget.js',
            'contacts_portal_type/static/src/widgets/partner_location_map/partner_location_map_widget.xml',
        ],
        'web.assets_frontend': [
            'contacts_portal_type/static/src/js/request_quote_map.js',
            'contacts_portal_type/static/src/js/hostess_tour.js',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/hostess_portal_model_access.xml',
        'security/hostess_portal_rules.xml',
        'views/shuttle_tour_hostess_views.xml',
        'views/res_partner_views.xml',
        'views/portal_templates.xml',
        'views/portal_role_pages.xml',
        'views/request_quote_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
