# -*- coding: utf-8 -*-
from odoo import fields, models


class ShuttleVehicleBrand(models.Model):
    _name = "shuttle.vehicle.brand"
    _description = "Vehicle Brand"
    _order = "sequence, name"

    name = fields.Char(string="Brand Name", required=True, translate=True)
    image = fields.Image(string="Brand Logo", max_width=256, max_height=256)
    sequence = fields.Integer(default=10)
