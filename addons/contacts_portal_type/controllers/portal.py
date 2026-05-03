# -*- coding: utf-8 -*-
from odoo import _
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalContactTypePortal(CustomerPortal):

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
