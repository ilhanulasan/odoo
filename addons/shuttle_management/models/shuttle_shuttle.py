# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ShuttleShuttle(models.Model):
    _name = "shuttle.shuttle"
    _description = "Shuttle"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "shuttle_no"

    _shuttle_route_unique = models.Constraint(
        "UNIQUE (route_id)",
        _("Each route can only be assigned to one shuttle."),
    )
    _shuttle_no_unique = models.Constraint(
        "UNIQUE (shuttle_no)",
        _("Shuttle No must be unique."),
    )

    brand_id = fields.Many2one(
        "shuttle.vehicle.brand",
        string="Brand",
        tracking=True,
    )
    brand_logo = fields.Image(
        related="brand_id.image",
        readonly=True,
    )
    shuttle_no = fields.Char(string="Shuttle No", required=True, tracking=True)
    route_id = fields.Many2one(
        "shuttle.route",
        string="Route ID",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    plate_number = fields.Char(string="Plate Nr", tracking=True)
    driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
        tracking=True,
        domain=[("is_company", "=", False)],
    )
    vehicle_model = fields.Char(string="Model", tracking=True)
    year = fields.Integer(string="Year", tracking=True)
    passenger_count = fields.Integer(string="Number of Passengers", tracking=True)
    picture = fields.Image(string="Shuttle Picture", max_width=1920, max_height=1920)
    description = fields.Text(string="Description")
    note_ids = fields.One2many(
        "shuttle.note",
        "shuttle_id",
        string="Notes",
    )
    tour_ids = fields.One2many(
        "shuttle.tour",
        "shuttle_id",
        string="Tours",
    )

    @api.constrains("year")
    def _check_year(self):
        for shuttle in self:
            if shuttle.year and (shuttle.year < 1900 or shuttle.year > 2100):
                raise ValidationError(_("Year must be between 1900 and 2100."))


class ShuttleNote(models.Model):
    _name = "shuttle.note"
    _description = "Shuttle Note"
    _order = "id desc"

    shuttle_id = fields.Many2one(
        "shuttle.shuttle",
        string="Shuttle",
        required=True,
        ondelete="cascade",
    )
    note = fields.Text(string="Note", required=True)
