from odoo import http
from odoo.http import request


class WebsiteBerkay(http.Controller):
    @http.route(
        ["/", "/en", "/en/", "/tr", "/tr/"],
        type="http",
        auth="public",
        website=True,
    )
    def index(self, **kw):
        # If user requested a language-prefixed URL, set session language so
        # Odoo and translations pick it up, then render the homepage.
        path = request.httprequest.path or ""
        if path.startswith("/en"):
            request.session['lang'] = 'en_US'
        elif path.startswith("/tr"):
            request.session['lang'] = 'tr_TR'
        return request.render("website_berkay.index", {})

