# -*- coding: utf-8 -*-
from odoo import _
from odoo.http import request, route
from odoo.tools.translate import LazyTranslate

from odoo.addons.portal.controllers.portal import CustomerPortal

_lt = LazyTranslate(__name__)


class PortalContactTypePortal(CustomerPortal):

    @route(
        ['/my', '/my/home'],
        type='http',
        auth='user',
        website=True,
        list_as_website_content=_lt('User Dashboard'),
    )
    def home(self, **kw):
        partner = request.env.user.partner_id
        if partner:
            ptype = partner.portal_contact_type
            if ptype == 'driver':
                return request.redirect('/driver')
            if ptype == 'parent':
                return request.redirect('/parents')
        return super().home(**kw)

    @route(['/driver'], type='http', auth='user', website=True, readonly=True)
    def portal_driver_home(self, **kw):
        values = self._prepare_portal_layout_values()
        values.update(
            {
                'page_name': 'driver',
                'portal_role_page_title': _('Driver'),
            }
        )
        return request.render('contacts_portal_type.portal_page_role_driver', values)

    @route(['/parents', '/Parents'], type='http', auth='user', website=True, readonly=True)
    def portal_parents_home(self, **kw):
        values = self._prepare_portal_layout_values()
        values.update(
            {
                'page_name': 'parents',
                'portal_role_page_title': _('Parents'),
            }
        )
        return request.render('contacts_portal_type.portal_page_role_parents', values)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if not partner or not partner.portal_contact_type:
            return values
        partner_fields = request.env['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get(partner.portal_contact_type, partner.portal_contact_type)
        values['portal_contact_welcome'] = _('Welcome %s') % label
        return values
