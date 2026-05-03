# -*- coding: utf-8 -*-
from odoo import _, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    portal_contact_type = fields.Selection(
        selection=[
            ('driver', _('Driver')),
            ('student', _('Student')),
            ('parent', _('Parent')),
            ('assistant', _('Assistant')),
            ('company_rep', _('Company Rep')),
            ('internal', _('Internal')),
        ],
        string=_('Portal Contact Type'),
        help=_('Role of this contact when exposed on the portal.'),
    )
