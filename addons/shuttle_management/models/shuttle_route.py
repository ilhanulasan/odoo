# -*- coding: utf-8 -*-
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ShuttleRoute(models.Model):
    _name = "shuttle.route"
    _description = "Shuttle Route"
    _order = "route_code"

    route_code = fields.Char(
        string="Route ID",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: "New",
    )
    route_no = fields.Char(string="No")
    name = fields.Char(string="Route Name", required=True)
    point_ids = fields.One2many(
        "shuttle.route.point",
        "route_id",
        string="Route Points",
    )
    shuttle_id = fields.Many2one(
        "shuttle.shuttle",
        string="Shuttle",
        compute="_compute_shuttle_id",
        inverse="_inverse_shuttle_id",
        readonly=False,
    )
    shuttle_plate_number = fields.Char(
        string="Shuttle Plate Nr",
        related="shuttle_id.plate_number",
        readonly=True,
    )
    shuttle_picture = fields.Image(
        string="Shuttle Picture",
        related="shuttle_id.picture",
        readonly=True,
    )
    tour_ids = fields.One2many(
        "shuttle.tour",
        "route_id",
        string="Tours",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("route_code", "New") == "New":
                vals["route_code"] = self.env["ir.sequence"].next_by_code(
                    "shuttle.route"
                ) or "New"
        return super().create(vals_list)

    def _compute_shuttle_id(self):
        Shuttle = self.env["shuttle.shuttle"]
        for route in self:
            shuttle = Shuttle.search([("route_id", "=", route.id)], limit=1)
            route.shuttle_id = shuttle

    def _inverse_shuttle_id(self):
        for route in self:
            linked = self.env["shuttle.shuttle"].search([("route_id", "=", route.id)])
            if route.shuttle_id:
                (linked - route.shuttle_id).write({"route_id": False})
                if route.shuttle_id.route_id != route:
                    route.shuttle_id.route_id = route
            else:
                linked.write({"route_id": False})

    def unlink(self):
        if self.env["shuttle.shuttle"].search_count([("route_id", "in", self.ids)]):
            raise ValidationError(_("You cannot delete routes that are linked to a shuttle."))
        return super().unlink()


class ShuttleRoutePoint(models.Model):
    _name = "shuttle.route.point"
    _description = "Shuttle Route Point"
    _order = "route_id, sequence, id"

    route_id = fields.Many2one(
        "shuttle.route",
        string="Route",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Label")
    latitude = fields.Float(
        string="Latitude",
        digits=(16, 7),
        required=True,
        default=41.015137,
    )
    longitude = fields.Float(
        string="Longitude",
        digits=(16, 7),
        required=True,
        default=29.118097,
    )
    address = fields.Char(
        string="Address",
        compute="_compute_address",
        store=True,
    )

    @api.depends("latitude", "longitude")
    def _compute_address(self):
        multi = len(self) > 1
        for idx, point in enumerate(self):
            if multi and idx:
                time.sleep(1.05)
            point.address = point._reverse_geocode_address()

    def _reverse_geocode_address(self):
        self.ensure_one()
        lat, lon = self.latitude, self.longitude
        if lat is False or lon is False:
            return False
        try:
            params = urllib.parse.urlencode(
                {
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "addressdetails": "0",
                }
            )
            url = f"https://nominatim.openstreetmap.org/reverse?{params}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "OdooShuttleManagement/19.0 (reverse geocoding; contact: admin)",
                    "Accept-Language": "en,tr",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                data = json.loads(response.read().decode())
            return data.get("display_name") or ""
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as e:
            _logger.warning("Reverse geocoding failed for point %s: %s", self.id, e)
            return ""

    @api.constrains("latitude", "longitude")
    def _check_coordinates(self):
        for point in self:
            if not (-90 <= point.latitude <= 90):
                raise ValidationError(_("Latitude must be between -90 and 90."))
            if not (-180 <= point.longitude <= 180):
                raise ValidationError(_("Longitude must be between -180 and 180."))
