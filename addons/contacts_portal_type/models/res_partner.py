# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_type = fields.Selection(
        selection=[
            ('person', _('Person')),
            ('company', _('Company')),
            ('school', _('School')),
            ('factory', _('Factory')),
        ],
        string=_('Contact Type'),
        default='company',
        required=True,
    )

    portal_contact_type = fields.Selection(
        selection=[
            ('driver', _('Driver')),
            ('student', _('Student')),
            ('parent', _('Parent')),
            ('hostess', _('Hostess')),
            ('school_rep', _('School Representative')),
            ('internal', _('Internal User')),
            ('vendor', _('Vendor')),
            ('customer', _('Customer')),
            ('factory_rep', _('Factory Representative')),
            ('factory_employee', _('Factory Employee')),
        ],
        string=_('Portal Contact Type'),
        help=_('Role of this contact when exposed on the portal.'),
    )

    date_of_birth = fields.Date(string=_('Date of Birth'))
    gender = fields.Selection(
        selection=[
            ('male', _('Male')),
            ('female', _('Female')),
        ],
        string=_('Gender'),
    )

    school_id = fields.Many2one(
        comodel_name='res.partner',
        string=_('School'),
        domain=[('contact_type', '=', 'school')],
    )
    school_avatar_128 = fields.Image(related='school_id.avatar_128', readonly=True)

    parent_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string=_('Parent'),
        domain=[('portal_contact_type', '=', 'parent'), ('contact_type', '=', 'person')],
    )
    parent_avatar_128 = fields.Image(related='parent_partner_id.avatar_128', readonly=True)
    dependants_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='parent_partner_id',
        string=_('Dependants'),
    )
    shift_hours_ids = fields.One2many(
        comodel_name='contacts_portal_type.shift_hours',
        inverse_name='partner_id',
        string=_('Shift Hours'),
    )
    shift_hours_display_ids = fields.Many2many(
        comodel_name='contacts_portal_type.shift_hours',
        string=_('Shift Hours (Display)'),
        compute='_compute_shift_hours_display',
        readonly=True,
    )

    @api.depends('school_id', 'parent_id', 'shift_hours_ids', 'contact_type', 'portal_contact_type')
    def _compute_shift_hours_display(self):
        for partner in self:
            # For Schools and Factories show own shift hours
            if partner.contact_type in ('school', 'factory'):
                partner.shift_hours_display_ids = partner.shift_hours_ids
            else:
                # For students/parents/factory employees show linked school's or parent's shift hours
                records = self.env['contacts_portal_type.shift_hours'].browse()
                if partner.school_id:
                    records = partner.school_id.shift_hours_ids
                elif partner.parent_id and partner.parent_id.contact_type == 'factory':
                    records = partner.parent_id.shift_hours_ids
                partner.shift_hours_display_ids = records
    is_handicapped = fields.Boolean(string=_('Handicapped'))
    is_deaf = fields.Boolean(string=_('Deaf'))
    is_blind = fields.Boolean(string=_('Blind'))
    is_allergic = fields.Boolean(string=_('Allergic'))
    # Shuttle Management integrations
    route_id = fields.Many2one(
        comodel_name='shuttle.route',
        string=_('Route Id'),
        ondelete='set null',
    )
    route_name = fields.Char(related='route_id.name', string=_('Route Name'), readonly=True)
    route_shuttle_id = fields.Many2one(related='route_id.shuttle_id', comodel_name='shuttle.shuttle', string=_('Assigned Shuttle'), readonly=True)
    route_shuttle_plate = fields.Char(related='route_id.shuttle_plate_number', string=_('Assigned Shuttle Plate'), readonly=True)
    route_shuttle_picture = fields.Image(related='route_id.shuttle_picture', string=_('Assigned Shuttle Picture'), readonly=True)

    @api.model
    def _default_currency_id(self):
        currency = self.env['res.currency'].search([('name', '=', 'TRY')], limit=1)
        return currency.id if currency else self.env.company.currency_id.id

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string=_('Annual Fee Currency'),
        default=lambda self: self._default_currency_id(),
        help=_('Annual shuttle fee is denominated in Turkish Lira (TRY).'),
    )
    annual_fee = fields.Monetary(string=_('Annual Fee'), currency_field='currency_id')

    @api.depends('parent_id', 'type')
    def _compute_type_address_label(self):
        super()._compute_type_address_label()
        for partner in self:
            if partner.type == 'contact' and partner.parent_id:
                partner.type_address_label = _('Address')

    @api.onchange('contact_type')
    def _onchange_contact_type(self):
        for partner in self:
            if partner.contact_type == 'person':
                partner.company_type = 'person'
                partner.is_company = False
            else:
                partner.company_type = 'company'
                partner.is_company = True
            if partner.contact_type != 'person':
                partner.portal_contact_type = False
                partner.school_id = False

    @api.onchange('company_type')
    def _onchange_company_type_sync_contact_type(self):
        for partner in self:
            if partner.company_type == 'person':
                partner.contact_type = 'person'
            elif partner.company_type == 'company' and partner.contact_type == 'person':
                partner.contact_type = 'company'


class ShiftHours(models.Model):
    _name = 'contacts_portal_type.shift_hours'
    _description = 'Contact Shift Hours'

    partner_id = fields.Many2one('res.partner', string=_('Contact'), required=True, ondelete='cascade')
    shift_type = fields.Selection(
        selection=[
            ('morning', _('Morning')),
            ('afternoon', _('Afternoon')),
            ('full_day', _('Full Day')),
            ('day_shift', _('Day Shift')),
            ('shift_1', _('Shift-1')),
            ('shift_2', _('Shift-2')),
            ('shift_3', _('Shift-3')),
        ],
        string=_('Shift Type'),
        required=True,
    )
    start_hour = fields.Float(string=_('Start Hour'))
    end_hour = fields.Float(string=_('End Hour'))
    monday = fields.Boolean(string=_('Monday'))
    tuesday = fields.Boolean(string=_('Tuesday'))
    wednesday = fields.Boolean(string=_('Wednesday'))
    thursday = fields.Boolean(string=_('Thursday'))
    friday = fields.Boolean(string=_('Friday'))
    saturday = fields.Boolean(string=_('Saturday'))
    sunday = fields.Boolean(string=_('Sunday'))
