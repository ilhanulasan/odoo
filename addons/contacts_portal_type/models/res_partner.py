# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.tools.translate import LazyTranslate

# Lazy translate factory for module-level strings (deferred until runtime/env is available)
_lt = LazyTranslate(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_type = fields.Selection(
        selection=[
            ('person', 'Person'),
            ('company', 'Company'),
            ('school', 'School'),
            ('factory', 'Factory'),
        ],
        string='Contact Type',
        default='company',
        required=True,
    )

    portal_contact_type = fields.Selection(
        selection=[
            ('driver', 'Driver'),
            ('student', 'Student'),
            ('parent', 'Parent'),
            ('hostess', 'Hostess'),
            ('school_rep', 'School Representative'),
            ('internal', 'Internal User'),
            ('vendor', 'Vendor'),
            ('customer', 'Customer'),
            ('factory_rep', 'Factory Representative'),
            ('factory_employee', 'Factory Employee'),
        ],
        string='Portal Contact Type',
        help='Role of this contact when exposed on the portal.',
    )

    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
        ],
        string='Gender',
    )

    school_id = fields.Many2one(
        comodel_name='res.partner',
        string='School',
        domain=[('contact_type', '=', 'school')],
    )
    school_avatar_128 = fields.Image(related='school_id.avatar_128', readonly=True)

    parent_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Parent ',
        domain=[('portal_contact_type', '=', 'parent'), ('contact_type', '=', 'person')],
    )
    parent_avatar_128 = fields.Image(related='parent_partner_id.avatar_128', readonly=True)
    dependants_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='parent_partner_id',
        string='Dependants',
    )
    shift_hours_ids = fields.One2many(
        comodel_name='contacts_portal_type.shift_hours',
        inverse_name='partner_id',
        string='Shift Hours',
    )
    shift_hours_display_ids = fields.Many2many(
        comodel_name='contacts_portal_type.shift_hours',
        string='Shift Hours (Display)',
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
    is_handicapped = fields.Boolean(string='Handicapped')
    is_deaf = fields.Boolean(string='Deaf')
    is_blind = fields.Boolean(string='Blind')
    is_allergic = fields.Boolean(string='Allergic')
    # Shuttle Management integrations
    route_id = fields.Many2one(
        comodel_name='shuttle.route',
        string='Route Id ',
        ondelete='set null',
    )
    route_name = fields.Char(related='route_id.name', string='Route Name', readonly=True)
    route_shuttle_id = fields.Many2one(related='route_id.shuttle_id', comodel_name='shuttle.shuttle', string='Assigned Shuttle', readonly=True)
    route_shuttle_plate = fields.Char(related='route_id.shuttle_plate_number', string='Assigned Shuttle Plate', readonly=True)
    route_shuttle_picture = fields.Image(related='route_id.shuttle_picture', string='Assigned Shuttle Picture', readonly=True)

    @api.model
    def _default_currency_id(self):
        currency = self.env['res.currency'].search([('name', '=', 'TRY')], limit=1)
        if not currency:
            currency = self.env['res.currency'].create({
                'name': 'TRY',
                'symbol': '₺',
                'rounding': 0.01,
                'position': 'after',
            })
        return currency.id

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Service Annual Fee Currency',
        default=lambda self: self._default_currency_id(),
        help='Annual shuttle fee is denominated in Turkish Lira (TRY).',
    )
    annual_fee = fields.Monetary(string='Service Annual Fee', currency_field='currency_id')

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

    partner_id = fields.Many2one('res.partner', string='Contact', required=True, ondelete='cascade')
    shift_type = fields.Selection(
        selection=[
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('full_day', 'Full Day'),
            ('day_shift', 'Day Shift'),
            ('shift_1', 'Shift-1'),
            ('shift_2', 'Shift-2'),
            ('shift_3', 'Shift-3'),
        ],
        string='Shift Type',
        required=True,
    )
    start_hour = fields.Float(string='Start Hour')
    end_hour = fields.Float(string='End Hour')
    monday = fields.Boolean(string='Monday')
    tuesday = fields.Boolean(string='Tuesday')
    wednesday = fields.Boolean(string='Wednesday')
    thursday = fields.Boolean(string='Thursday')
    friday = fields.Boolean(string='Friday')
    saturday = fields.Boolean(string='Saturday')
    sunday = fields.Boolean(string='Sunday')
