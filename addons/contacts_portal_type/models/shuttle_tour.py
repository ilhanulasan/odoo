# -*- coding: utf-8 -*-
from odoo import fields, models


class ShuttleTour(models.Model):
    _inherit = 'shuttle.tour'

    hostess_id = fields.Many2one(
        'res.partner',
        string='Hostess',
        ondelete='set null',
        index=True,
        help='Portal hostess who started this tour from the website.',
    )
