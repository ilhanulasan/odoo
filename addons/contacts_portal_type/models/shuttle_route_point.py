# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ShuttleRoutePoint(models.Model):
    _inherit = 'shuttle.route.point'

    student_partner_id = fields.Many2one(
        'res.partner',
        string='Student',
        domain="[('portal_contact_type', '=', 'student')]",
        ondelete='set null',
        help='Pick a student contact to use their saved map coordinates as this stop.',
    )

    @api.model
    def _lat_lng_from_partner(self, partner):
        if not partner:
            return None, None
        lat = partner.partner_latitude
        lng = partner.partner_longitude
        if lat is False or lng is False or lat is None or lng is None:
            return None, None
        try:
            latf = float(lat)
            lngf = float(lng)
        except (TypeError, ValueError):
            return None, None
        if latf == 0.0 and lngf == 0.0:
            return None, None
        return latf, lngf

    @api.onchange('student_partner_id')
    def _onchange_student_partner_id(self):
        for point in self:
            if not point.student_partner_id:
                continue
            lat, lng = point._lat_lng_from_partner(point.student_partner_id)
            if lat is not None:
                point.latitude = lat
                point.longitude = lng
            if not point.name:
                point.name = point.student_partner_id.display_name

    @api.model_create_multi
    def create(self, vals_list):
        Partner = self.env['res.partner']
        for vals in vals_list:
            sid = vals.get('student_partner_id')
            if sid:
                lat, lng = self._lat_lng_from_partner(Partner.browse(sid))
                if lat is not None:
                    vals['latitude'] = lat
                    vals['longitude'] = lng
        records = super().create(vals_list)
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'student_partner_id' in vals:
            for point in self:
                point._sync_coordinates_from_student()
        return res

    def _sync_coordinates_from_student(self):
        self.ensure_one()
        if not self.student_partner_id:
            return
        lat, lng = self._lat_lng_from_partner(self.student_partner_id)
        if lat is None:
            return
        if (
            abs((self.latitude or 0.0) - lat) > 1e-9
            or abs((self.longitude or 0.0) - lng) > 1e-9
        ):
            super(ShuttleRoutePoint, self).write({'latitude': lat, 'longitude': lng})

    @api.constrains('student_partner_id')
    def _check_student_has_map_coordinates(self):
        for point in self:
            if not point.student_partner_id:
                continue
            lat, _lng = point._lat_lng_from_partner(point.student_partner_id)
            if lat is None:
                raise ValidationError(
                    _(
                        'Selected student "%(name)s" has no map coordinates. Open the contact, '
                        'set the address location on the map, then try again.'
                    )
                    % {'name': point.student_partner_id.display_name}
                )
