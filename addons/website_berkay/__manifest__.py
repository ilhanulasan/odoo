{
    "name": "Website Berkay",
    "summary": "Static homepage cloned from berkayturizm.com",
    "description": "A simple Odoo website module providing a static homepage that mimics Berkay Turizm.",
    "version": "19.0.1.0.0",
    "author": "AI Assistant",
    "category": "Website",
    "depends": ["website"],
    "data": [
        "views/templates.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            "website_berkay/static/src/css/style.css"
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False
}
