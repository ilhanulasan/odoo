# -*- coding: utf-8 -*-
import logging
import re
from datetime import date

from odoo import _, fields, http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


def _safe_float(val):
    try:
        if val is None or val == '':
            return None
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_date(val):
    if not val:
        return None
    try:
        return fields.Date.from_string(val.strip())
    except (ValueError, TypeError):
        return None


class RequestQuoteController(http.Controller):

    def _form_env(self):
        lang = getattr(request, 'lang', None)
        if lang and request.env.context.get('lang') != lang.code:
            return request.env(context={**request.env.context, 'lang': lang.code})
        return request.env

    def _render_form(self, schools, countries, errors=None, form_data=None):
        values = {
            'schools': schools,
            'countries': countries,
            'errors': errors or {},
            'form': form_data or {},
            'error_message': None,
        }
        return request.render('contacts_portal_type.request_quote_page', values)

    @http.route(
        ['/request-quote', '/requestquote'],
        type='http',
        auth='public',
        website=True,
        methods=['GET'],
        readonly=True,
    )
    def request_quote_get(self, **kw):
        env = self._form_env()
        Partner = env['res.partner'].sudo()
        schools = Partner.search([('contact_type', '=', 'school')], order='name')
        countries = env['res.country'].sudo().search([], order='name')
        return self._render_form(schools, countries)

    @http.route(
        ['/request-quote/submit', '/requestquote/submit'],
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        readonly=False,
    )
    def request_quote_submit(self, **post):
        env = self._form_env()
        Partner = env['res.partner'].sudo()
        schools = Partner.search([('contact_type', '=', 'school')], order='name')
        countries = env['res.country'].sudo().search([], order='name')

        errors = {}
        form = {
            'parent_first_name': (post.get('parent_first_name') or '').strip(),
            'parent_surname': (post.get('parent_surname') or '').strip(),
            'phone': (post.get('phone') or '').strip(),
            'email': (post.get('email') or '').strip(),
            'student_name': (post.get('student_name') or '').strip(),
            'student_gender': (post.get('student_gender') or '').strip(),
            'student_dob': (post.get('student_dob') or '').strip(),
            'school_id': (post.get('school_id') or '').strip(),
            'street': (post.get('street') or '').strip(),
            'street2': (post.get('street2') or '').strip(),
            'city': (post.get('city') or '').strip(),
            'zip': (post.get('zip') or '').strip(),
            'country_id': (post.get('country_id') or '').strip(),
            'partner_latitude': (post.get('partner_latitude') or '').strip(),
            'partner_longitude': (post.get('partner_longitude') or '').strip(),
        }

        def _req(label, key):
            if not form.get(key):
                errors[key] = label

        _req(_('First name is required.'), 'parent_first_name')
        _req(_('Surname is required.'), 'parent_surname')
        _req(_('Phone is required.'), 'phone')
        _req(_('Email is required.'), 'email')
        if form['email'] and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', form['email']):
            errors['email'] = _('Please enter a valid email address.')
        _req(_('Student name is required.'), 'student_name')
        if form['student_gender'] not in ('male', 'female'):
            errors['student_gender'] = _('Student gender is required.')
        student_dob = _parse_date(form['student_dob'])
        if not student_dob:
            errors['student_dob'] = _('Student date of birth is required.')
        elif student_dob > date.today():
            errors['student_dob'] = _('Date of birth cannot be in the future.')

        school_id_int = None
        if not form['school_id']:
            errors['school_id'] = _('School is required.')
        else:
            try:
                school_id_int = int(form['school_id'])
            except (TypeError, ValueError):
                errors['school_id'] = _('Invalid school.')
            else:
                school_rec = Partner.browse(school_id_int)
                if not school_rec.exists() or school_rec.contact_type != 'school':
                    errors['school_id'] = _('Invalid school.')

        _req(_('Street is required.'), 'street')
        _req(_('City is required.'), 'city')

        country_id_int = None
        if form['country_id']:
            try:
                country_id_int = int(form['country_id'])
            except (TypeError, ValueError):
                errors['country_id'] = _('Invalid country.')
            if country_id_int and not env['res.country'].sudo().browse(country_id_int).exists():
                errors['country_id'] = _('Invalid country.')

        lat = _safe_float(form.get('partner_latitude') or post.get('partner_latitude'))
        lng = _safe_float(form.get('partner_longitude') or post.get('partner_longitude'))
        if lat is None or lng is None:
            errors['map'] = _('Please place a pin on the map for your address.')
        elif not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            errors['map'] = _('Invalid map coordinates.')

        if errors:
            values = {
                'schools': schools,
                'countries': countries,
                'errors': errors,
                'form': form,
                'error_message': _('Please correct the errors below.'),
            }
            return request.render('contacts_portal_type.request_quote_page', values)

        parent_name = f"{form['parent_first_name']} {form['parent_surname']}".strip()

        address_vals = {
            'street': form['street'],
            'street2': form['street2'] or False,
            'city': form['city'],
            'zip': form['zip'] or False,
            'country_id': country_id_int or False,
            'partner_latitude': lat,
            'partner_longitude': lng,
        }

        try:
            parent = Partner.create({
                'name': parent_name,
                'phone': form['phone'],
                'email': form['email'],
                'is_company': False,
                'contact_type': 'person',
                'portal_contact_type': 'parent',
                **address_vals,
            })
            student = Partner.create({
                'name': form['student_name'],
                'is_company': False,
                'contact_type': 'person',
                'portal_contact_type': 'student',
                'gender': form['student_gender'],
                'date_of_birth': student_dob,
                'school_id': school_id_int,
                'parent_partner_id': parent.id,
                **address_vals,
            })
            order = env['sale.order'].sudo().create({
                'partner_id': parent.id,
                'origin': 'Website: Request quote',
            })
            _logger.info(
                'request_quote: created parent=%s student=%s sale_order=%s',
                parent.id, student.id, order.id,
            )
        except ValidationError as e:
            _logger.exception('request_quote validation failed')
            values = {
                'schools': schools,
                'countries': countries,
                'errors': {'_fatal': str(e)},
                'form': form,
                'error_message': str(e),
            }
            return request.render('contacts_portal_type.request_quote_page', values)
        except Exception:
            _logger.exception('request_quote failed')
            values = {
                'schools': schools,
                'countries': countries,
                'errors': {},
                'form': form,
                'error_message': _(
                    'We could not submit your request. Please try again later or contact us.'
                ),
            }
            return request.render('contacts_portal_type.request_quote_page', values)

        return request.redirect('/request-quote/thank-you')

    @http.route(
        ['/request-quote/thank-you', '/requestquote/thank-you'],
        type='http',
        auth='public',
        website=True,
        methods=['GET'],
        readonly=True,
    )
    def request_quote_thanks(self, **kw):
        return request.render('contacts_portal_type.request_quote_thank_you', {})
