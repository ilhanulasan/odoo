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


class ShuttleTour(models.Model):
    _name = "shuttle.tour"
    _description = "Shuttle Tour"
    _order = "tour_no"

    tour_no = fields.Char(string="No.", required=True, copy=False, readonly=True, default=lambda self: "New")
    date = fields.Date(string="Date", required=True)
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    total_duration = fields.Float(string="Total Duration (hours)", compute="_compute_total_duration", store=True)
    shuttle_id = fields.Many2one("shuttle.shuttle", string="Shuttle", ondelete="set null")
    route_id = fields.Many2one("shuttle.route", string="Route", ondelete="set null")
    point_ids = fields.One2many("shuttle.tour.point", "tour_id", string="Tour Points")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("tour_no", "New") == "New":
                vals["tour_no"] = self.env["ir.sequence"].next_by_code("shuttle.tour") or "New"
        return super().create(vals_list)

    @api.depends("start_time", "end_time")
    def _compute_total_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                # total duration in hours
                rec.total_duration = round(delta.total_seconds() / 3600.0, 3)
            else:
                rec.total_duration = 0.0


class ShuttleTourPoint(models.Model):
    _name = "shuttle.tour.point"
    _description = "Shuttle Tour Point"
    _order = "tour_id, datetime, id"

    tour_id = fields.Many2one("shuttle.tour", string="Tour", required=True, ondelete="cascade")
    datetime = fields.Datetime(string="DateTime", required=True, default=fields.Datetime.now)
    latitude = fields.Float(string="Latitude", digits=(16, 7), required=True, default=41.015137)
    longitude = fields.Float(string="Longitude", digits=(16, 7), required=True, default=29.118097)
    address = fields.Char(string="Address", compute="_compute_address", store=True)

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
            _logger.warning("Reverse geocoding failed for tour point %s: %s", self.id, e)
            return ""

    @api.constrains("latitude", "longitude")
    def _check_coordinates(self):
        for point in self:
            if not (-90 <= point.latitude <= 90):
                raise ValidationError(_("Latitude must be between -90 and 90."))
            if not (-180 <= point.longitude <= 180):
                raise ValidationError(_("Longitude must be between -180 and 180."))

