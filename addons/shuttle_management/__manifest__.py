# -*- coding: utf-8 -*-
{
    "name": "Shuttle Management",
    "version": "19.0.4.0.0",
    "category": "Operations",
    "summary": "Shuttles, routes, and route points on a map",
    "depends": ["base", "contacts", "mail"],
    "data": [
        "security/shuttle_management_security.xml",
        "security/ir.model.access.csv",
        "data/shuttle_route_sequence.xml",
        "data/shuttle_vehicle_brand_data.xml",
        "views/shuttle_vehicle_brand_views.xml",
        "views/shuttle_route_views.xml",
        "views/shuttle_shuttle_views.xml",
        "views/shuttle_tour_views.xml",
        "views/shuttle_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "shuttle_management/static/src/views/widgets/route_map/**/*",
        ],
    },
    "author": "Odoo Community",
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
