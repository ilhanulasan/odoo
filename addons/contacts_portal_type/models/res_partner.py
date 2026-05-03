# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    portal_contact_type = fields.Selection(
        selection=[
            ('driver', 'Driver'),
            ('student', 'Student'),
            ('parent', 'Parent'),
            ('assistant', 'Assistant'),
            ('company_rep', 'Company Rep'),
            ('internal', 'Internal'),
        ],
        string='Portal Contact Type',
        help='Role of this contact when exposed on the portal.',
    )
