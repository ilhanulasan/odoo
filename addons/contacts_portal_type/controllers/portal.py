# -*- coding: utf-8 -*-
import json
import logging
import random

from markupsafe import Markup, escape

from odoo import fields
from odoo.http import request, route
from odoo.tools.translate import LazyTranslate

from odoo.addons.portal.controllers.portal import CustomerPortal

_lt = LazyTranslate(__name__)

_logger = logging.getLogger(__name__)

# Truncate JSON in odoo.log so one line stays readable for large payloads.
_PARENT_PORTAL_JSON_LOG_MAX = 2000


class PortalContactTypePortal(CustomerPortal):

    def _portal_translation_env(self):
        """Environment for ``_()`` / translations on frontend routes.

        ``http_routing`` stores the resolved language on ``request.lang`` (URL,
        ``frontend_lang`` cookie, …). That can differ from ``request.env.context``
        on some portal requests, so ``request.env._()`` would not load Turkish
        even after picking it in the top bar. Sync context to ``request.lang``.
        """
        lang = getattr(request, "lang", None)
        if not lang:
            return request.env
        code = lang.code
        if code and request.env.context.get("lang") != code:
            return request.env(context={**request.env.context, "lang": code})
        return request.env

    @route(
        ['/my', '/my/home'],
        type='http',
        auth='user',
        website=True,
        list_as_website_content=_lt('User Dashboard'),
    )
    def home(self, **kw):
        partner = request.env.user.partner_id
        if partner:
            ptype = partner.portal_contact_type
            if ptype:
                mapping = {
                    'driver': '/drivers',
                    'student': '/students',
                    'parent': '/parents2',
                    'hostess': '/users',
                    'school_rep': '/school_representative',
                    'internal': '/internal',
                    'vendor': '/vendors',
                    'customer': '/customers',
                    'factory_rep': '/factory_representatives',
                    'factory_employee': '/factory_employees',
                }
                path = mapping.get(ptype)
                if path:
                    return request.redirect(path)
        return super().home(**kw)

    @route(['/drivers'], type='http', auth='user', website=True, readonly=True)
    def portal_driver_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        values.update(
            {
                'page_name': 'drivers',
                'portal_drivers_header': tenv._('Servis Soförleri Portalı'),
                'portal_drivers_btn_start_tour': tenv._('Tur Başlat'),
                'portal_drivers_btn_enroll_student': tenv._('Yeni Öğrenci Kaydı'),
            }
        )
        return request.render('contacts_portal_type.portal_page_role_driver', values)

    @route(['/parents2', '/Parents2'], type='http', auth='user', website=True, readonly=True)
    def portal_parents_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        partner = request.env.user.partner_id
        Partner = tenv['res.partner']
        portal_parent_students = Partner.browse()
        domain = None
        count_sudo = None
        if 'parent_partner_id' not in Partner._fields:
            _logger.warning(
                'contacts_portal_type parent_portal: res.partner has no parent_partner_id; '
                'students list empty. user=%s uid=%s partner_id=%s',
                request.env.user.login,
                request.env.uid,
                partner.id,
            )
        else:
            domain = [('parent_partner_id', '=', partner.id)]
            count_sudo = Partner.sudo().search_count(domain)
            # Portal users often cannot read other contacts (record rules). Only children
            # linked to this parent's partner id are loaded — same domain as above.
            portal_parent_students = Partner.sudo().search(domain)
            if count_sudo != len(portal_parent_students):
                _logger.warning(
                    'contacts_portal_type parent_portal: unexpected student count mismatch. '
                    'partner_id=%s sudo_count=%s resolved_count=%s ids=%s',
                    partner.id,
                    count_sudo,
                    len(portal_parent_students),
                    portal_parent_students.ids,
                )

        res_list = []
        for c in portal_parent_students:
            school = getattr(c, 'school_id', False)
            route_id = getattr(c, 'route_id', False)
            route = getattr(c, 'route', False)
            shuttle_id = getattr(c, 'shuttle_id', False)
            shuttle = getattr(c, 'shuttle', False)
            birth = (
                getattr(c, 'birth_date', False)
                or getattr(c, 'birthday', False)
                or getattr(c, 'date_of_birth', False)
            )
            res_list.append(
                {
                    'id': c.id,
                    'name': c.name,
                    'birth_date': str(birth) if birth else False,
                    'school': school.name if school else False,
                    'route': route_id.name if route_id else (route or False),
                    'shuttle': shuttle_id.name if shuttle_id else (shuttle or False),
                }
            )
        students_json = json.dumps(res_list, ensure_ascii=False)
        json_log = students_json
        if len(json_log) > _PARENT_PORTAL_JSON_LOG_MAX:
            json_log = json_log[:_PARENT_PORTAL_JSON_LOG_MAX] + '...(truncated)'
        _logger.warning(
            'contacts_portal_type parent_portal: path=/parents2 user=%r uid=%s '
            'partner_id=%s portal_contact_type=%r domain=%s '
            'sudo_count=%s students_loaded=%s student_ids=%s json=%s',
            request.env.user.login,
            request.env.uid,
            partner.id,
            partner.portal_contact_type,
            domain,
            count_sudo,
            len(portal_parent_students),
            portal_parent_students.ids,
            json_log,
        )

        student_count = len(portal_parent_students)
        student_rows = []
        for c in portal_parent_students:
            name = escape(str(c.display_name or c.name or ''))
            student_rows.append(
                Markup('<li class="list-group-item">%s <small class="text-muted">(id %s)</small></li>')
                % (name, c.id)
            )
        portal_student_simple_html = (
            Markup('<ul class="list-group list-group-flush border rounded">')
            + Markup().join(student_rows)
            + Markup('</ul>')
            if student_rows
            else Markup('')
        )
        portal_parent_student_debug = Markup(
            '[contacts_portal_type] parent_partner_id=%s student_count=%s student_ids=%s'
            % (partner.id, student_count, portal_parent_students.ids)
        )

        values.update(
            {
                'page_name': 'parents2',
                'portal_role_page_title': tenv._('Parents'),
                'portal_parent_students': portal_parent_students,
                # Plain ids for QWeb: recordsets passed through nested t-call slots can
                # lose rows for portal users; browse(sudo) in the template is reliable.
                'portal_parent_student_ids': list(portal_parent_students.ids),
                'portal_parent_student_count': student_count,
                'portal_student_simple_html': portal_student_simple_html,
                'portal_parent_student_debug': portal_parent_student_debug,
                'portal_parent_students_json': students_json,
            }
        )
        return request.render('contacts_portal_type.portal_page_role_parents', values)

    @route(['/students'], type='http', auth='user', website=True, readonly=True)
    def portal_students_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        # Lookup label for display
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('student', 'student')
        values.update({'page_name': 'students', 'portal_role_page_title': tenv._('Welcome %s') % label})
        return request.render('contacts_portal_type.portal_page_role_student', values)

    @route(['/hostess'], type='http', auth='user', website=True, readonly=True)
    def portal_hostess_home(self, **kw):
        return request.redirect('/users')

    def _hostess_portal_partner(self):
        """Partner for the current user if and only if portal role is hostess.

        Checks partners linked via ``user_ids``, ``user.partner_id``, and
        ``user.commercial_partner_id``. ``portal_contact_type`` is read with
        ``sudo`` because portal ACL may hide it on the bare recordset.
        """
        user = request.env.user
        if not user or user._is_public():
            return None
        PartnerSudo = request.env['res.partner'].sudo()
        uid = user.id
        candidates = PartnerSudo.search([('user_ids', 'in', [uid])])
        seen = set(candidates.ids)
        ordered = list(candidates.ids)
        pr = user.partner_id
        if pr and pr.id not in seen:
            seen.add(pr.id)
            ordered.append(pr.id)
        if pr:
            cp = pr.commercial_partner_id
            if cp and cp.id not in seen:
                seen.add(cp.id)
                ordered.append(cp.id)
        for pid in ordered:
            p = PartnerSudo.browse(pid)
            if p.exists() and p.portal_contact_type == 'hostess':
                return request.env['res.partner'].browse(pid)
        _logger.warning(
            'contacts_portal_type hostess: forbidden uid=%s login=%r checked_partner_ids=%s',
            uid,
            user.login,
            ordered,
        )
        return None

    def _hostess_login_required_response(self):
        tenv = self._portal_translation_env()
        return request.make_json_response(
            {
                'ok': False,
                'code': 'login_required',
                'error': tenv._('Please sign in to continue.'),
            },
            status=401,
        )

    def _hostess_tour_api_begin(self):
        """Return ``(partner, None)`` or ``(None, error_response)`` for JSON tour APIs."""
        if request.env.user._is_public():
            return None, self._hostess_login_required_response()
        partner = self._hostess_portal_partner()
        if not partner:
            return None, self._hostess_portal_forbidden_response()
        return partner, None

    def _hostess_portal_forbidden_response(self):
        tenv = self._portal_translation_env()
        return request.make_json_response(
            {
                'ok': False,
                'code': 'not_hostess',
                'error': tenv._(
                    'This action is only available for portal users whose contact is set to Hostess.'
                ),
            },
            status=403,
        )

    def _hostess_portal_json(self):
        try:
            raw = request.httprequest.get_data(cache=False, as_text=True)
            return json.loads(raw) if raw else {}
        except (json.JSONDecodeError, TypeError, ValueError):
            return {}

    def _hostess_coords_from_route_destination(self, route):
        if not route:
            return 41.015137, 29.118097
        points = route.point_ids.sorted(key=lambda p: (p.sequence, p.id))
        if not points:
            return 41.015137, 29.118097
        last = points[-1]
        return last.latitude, last.longitude

    def _random_anatolian_istanbul_latlon(self):
        """Approximate urban Asian-side Istanbul (east of the Bosporus)."""
        lat = round(random.uniform(40.875, 41.162), 7)
        lon = round(random.uniform(29.085, 29.398), 7)
        return lat, lon

    def _parse_optional_latlon(self, payload):
        """Return (lat, lon) floats or None if missing/invalid."""
        lat = payload.get('latitude')
        lon = payload.get('longitude')
        if lat is None or lon is None or lat == '' or lon == '':
            return None
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            return None
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return None
        return lat, lon

    def _prepare_hostess_users_values(self):
        tenv = self._portal_translation_env()
        partner = self._hostess_portal_partner()
        if not partner:
            return None
        Shuttle = tenv['shuttle.shuttle']
        Route = tenv['shuttle.route']
        Tour = tenv['shuttle.tour']
        routes = Route.search([], order='name')
        shuttles = Shuttle.search([], order='shuttle_no')
        open_tour = Tour.search(
            [('hostess_id', '=', partner.id), ('end_time', '=', False)],
            order='id desc',
            limit=1,
        )
        routes_payload = [{'id': r.id, 'name': r.display_name} for r in routes]
        shuttles_payload = [
            {
                'id': s.id,
                'name': s.display_name,
                'route_id': s.route_id.id if s.route_id else None,
            }
            for s in shuttles
        ]
        open_payload = None
        if open_tour:
            open_payload = {
                'id': open_tour.id,
                'tour_no': open_tour.tour_no,
                'route_id': open_tour.route_id.id if open_tour.route_id else None,
                'shuttle_id': open_tour.shuttle_id.id if open_tour.shuttle_id else None,
            }
        tour_i18n = {
            'geolocation_unsupported': tenv._(
                'Geolocation is not supported by this browser.'
            ),
            'invalid_response_refresh': tenv._(
                'Invalid response from server. Try refreshing the page.'
            ),
            'request_failed_generic': tenv._('Request failed'),
            'request_failed_sign_out': tenv._(
                'Request failed (%s). If the problem continues, sign out and sign in again.'
            ),
            'unexpected_non_json': tenv._(
                'Unexpected response from server (not JSON). Try refreshing the page.'
            ),
            'select_route_and_shuttle': tenv._('Please select a route and a shuttle.'),
            'getting_location': tenv._('Getting location…'),
            'random_istanbul_fallback': tenv._(
                'No location; using a random point on the Anatolian side of Istanbul.'
            ),
            'tour_started': tenv._('Tour %s started.'),
            'could_not_start': tenv._('Could not start tour. Try again.'),
            'tour_point_added': tenv._('Tour point added.'),
            'could_not_add_point': tenv._('Could not add point.'),
            'tour_finished': tenv._('Tour finished. Destination recorded.'),
            'could_not_finish': tenv._('Could not finish tour.'),
            'notes_saved': tenv._('Notes saved.'),
            'could_not_save_notes': tenv._('Could not save notes.'),
        }
        hostess_json = json.dumps(
            {
                'csrf': request.csrf_token(),
                'routes': routes_payload,
                'shuttles': shuttles_payload,
                'openTour': open_payload,
                'i18n': tour_i18n,
            },
            ensure_ascii=True,
        )
        values = self._prepare_portal_layout_values()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('hostess', 'hostess')
        values.update(
            {
                'page_name': 'users',
                'portal_role_page_title': tenv._('Welcome %s') % label,
                'partner': partner,
                'portal_routes': routes,
                'portal_shuttles': shuttles,
                'open_hostess_tour': open_tour,
                'hostess_tour_json': Markup(hostess_json),
                'hostess_ui': {
                    'page_heading': tenv._('Shuttle tour'),
                    'active_tour_prefix': tenv._('Active tour:'),
                    'no_active_tour': tenv._(
                        'No active tour. Select a route and shuttle, then start.'
                    ),
                    'label_route': tenv._('Route'),
                    'label_shuttle': tenv._('Shuttle'),
                    'select_route': tenv._('Select route...'),
                    'select_shuttle': tenv._('Select shuttle...'),
                    'btn_start': tenv._('Start Tour'),
                    'btn_add_point': tenv._('Add Tour Point'),
                    'btn_finish': tenv._('Finish Tour'),
                    'label_notes': tenv._('Notes'),
                    'placeholder_notes': tenv._('Tour notes'),
                    'btn_save_notes': tenv._('Save notes'),
                },
            }
        )
        return values

    @route(['/users'], type='http', auth='user', website=True, readonly=True)
    def portal_hostess_users(self, **kw):
        values = self._prepare_hostess_users_values()
        if values is None:
            return request.redirect('/my')
        return request.render('contacts_portal_type.portal_page_role_hostess', values)

    @route(
        [
            '/portal/api/hostess/tour/start',
            '/users/tour/start',
        ],
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        readonly=False,
        csrf=False,
    )
    def portal_hostess_tour_start(self, **kwargs):
        partner, err = self._hostess_tour_api_begin()
        if err is not None:
            return err
        tenv = self._portal_translation_env()
        payload = self._hostess_portal_json()
        tour_env = request.env['shuttle.tour']
        if tour_env.search_count(
            [('hostess_id', '=', partner.id), ('end_time', '=', False)]
        ):
            return request.make_json_response(
                {'ok': False, 'error': tenv._('You already have an active tour. Finish it before starting a new one.')},
                status=400,
            )
        try:
            route_id = int(payload.get('route_id'))
            shuttle_id = int(payload.get('shuttle_id'))
        except (TypeError, ValueError):
            return request.make_json_response(
                {'ok': False, 'error': tenv._('Invalid route or shuttle.')},
                status=400,
            )
        coords = self._parse_optional_latlon(payload)
        if coords is None:
            latitude, longitude = self._random_anatolian_istanbul_latlon()
            _logger.info(
                'hostess tour start: no valid location in payload; using random Anatolian Istanbul point '
                '(%s, %s) for partner %s',
                latitude,
                longitude,
                partner.id,
            )
        else:
            latitude, longitude = coords
        Route = request.env['shuttle.route'].browse(route_id)
        Shuttle = request.env['shuttle.shuttle'].browse(shuttle_id)
        if not Route.exists() or not Shuttle.exists() or Shuttle.route_id.id != Route.id:
            return request.make_json_response(
                {'ok': False, 'error': tenv._('The selected shuttle does not match the route.')},
                status=400,
            )
        now_dt = fields.Datetime.now()
        today = fields.Date.context_today(request.env.user)
        Point = request.env['shuttle.tour.point']
        tour = tour_env.create(
            {
                'date': today,
                'start_time': now_dt,
                'shuttle_id': shuttle_id,
                'route_id': route_id,
                'hostess_id': partner.id,
            }
        )
        Point.create(
            {
                'tour_id': tour.id,
                'datetime': now_dt,
                'latitude': latitude,
                'longitude': longitude,
            }
        )
        return request.make_json_response(
            {
                'ok': True,
                'tour_id': tour.id,
                'tour_no': tour.tour_no,
            }
        )

    @route(
        [
            '/portal/api/hostess/tour/point',
            '/users/tour/point',
        ],
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        readonly=False,
        csrf=False,
    )
    def portal_hostess_tour_add_point(self, **kwargs):
        partner, err = self._hostess_tour_api_begin()
        if err is not None:
            return err
        tenv = self._portal_translation_env()
        payload = self._hostess_portal_json()
        try:
            tour_id = int(payload.get('tour_id'))
            latitude = float(payload.get('latitude'))
            longitude = float(payload.get('longitude'))
        except (TypeError, ValueError):
            return request.make_json_response(
                {'ok': False, 'error': tenv._('Invalid tour or coordinates.')},
                status=400,
            )
        tour = request.env['shuttle.tour'].browse(tour_id)
        if (
            not tour.exists()
            or tour.hostess_id.id != partner.id
            or tour.end_time
        ):
            return request.make_json_response(
                {'ok': False, 'error': tenv._('Tour not found or already finished.')},
                status=400,
            )
        request.env['shuttle.tour.point'].create(
            {
                'tour_id': tour.id,
                'datetime': fields.Datetime.now(),
                'latitude': latitude,
                'longitude': longitude,
            }
        )
        return request.make_json_response({'ok': True})

    @route(
        [
            '/portal/api/hostess/tour/finish',
            '/users/tour/finish',
        ],
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        readonly=False,
        csrf=False,
    )
    def portal_hostess_tour_finish(self, **kwargs):
        partner, err = self._hostess_tour_api_begin()
        if err is not None:
            return err
        tenv = self._portal_translation_env()
        payload = self._hostess_portal_json()
        try:
            tour_id = int(payload.get('tour_id'))
        except (TypeError, ValueError):
            return request.make_json_response(
                {'ok': False, 'error': tenv._('Invalid tour.')},
                status=400,
            )
        tour = request.env['shuttle.tour'].browse(tour_id)
        if not tour.exists() or tour.hostess_id.id != partner.id or tour.end_time:
            return request.make_json_response(
                {'ok': False, 'error': tenv._('Tour not found or already finished.')},
                status=400,
            )
        try:
            lat = float(payload.get('latitude'))
            lon = float(payload.get('longitude'))
        except (TypeError, ValueError):
            lat, lon = self._hostess_coords_from_route_destination(tour.route_id)
        now_dt = fields.Datetime.now()
        request.env['shuttle.tour.point'].create(
            {
                'tour_id': tour.id,
                'datetime': now_dt,
                'latitude': lat,
                'longitude': lon,
            }
        )
        tour.write({'end_time': now_dt})
        return request.make_json_response({'ok': True})

    @route(
        [
            '/portal/api/hostess/tour/notes',
            '/users/tour/notes',
        ],
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        readonly=False,
        csrf=False,
    )
    def portal_hostess_tour_notes(self, **kwargs):
        partner, err = self._hostess_tour_api_begin()
        if err is not None:
            return err
        tenv = self._portal_translation_env()
        payload = self._hostess_portal_json()
        try:
            tour_id = int(payload.get('tour_id'))
        except (TypeError, ValueError):
            return request.make_json_response(
                {'ok': False, 'error': tenv._('Invalid tour.')},
                status=400,
            )
        tour = request.env['shuttle.tour'].browse(tour_id)
        if not tour.exists() or tour.hostess_id.id != partner.id:
            return request.make_json_response(
                {'ok': False, 'error': tenv._('Tour not found.')},
                status=400,
            )
        notes = payload.get('notes')
        if notes is None:
            notes = ''
        elif not isinstance(notes, str):
            notes = str(notes)
        tour.write({'notes': notes})
        return request.make_json_response({'ok': True})

    @route(['/school_representative'], type='http', auth='user', website=True, readonly=True)
    def portal_school_rep_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('school_rep', 'school_rep')
        values.update({'page_name': 'school_representative', 'portal_role_page_title': tenv._('Welcome %s') % label})
        return request.render('contacts_portal_type.portal_page_role_school_rep', values)

    @route(['/internal'], type='http', auth='user', website=True, readonly=True)
    def portal_internal_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('internal', 'internal')
        values.update({'page_name': 'internal', 'portal_role_page_title': tenv._('Welcome %s') % label})
        return request.render('contacts_portal_type.portal_page_role_internal', values)

    @route(['/vendors'], type='http', auth='user', website=True, readonly=True)
    def portal_vendors_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('vendor', 'vendor')
        values.update({'page_name': 'vendors', 'portal_role_page_title': tenv._('Welcome %s') % label})
        return request.render('contacts_portal_type.portal_page_role_vendor', values)

    @route(['/customers'], type='http', auth='user', website=True, readonly=True)
    def portal_customers_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('customer', 'customer')
        values.update({'page_name': 'customers', 'portal_role_page_title': tenv._('Welcome %s') % label})
        return request.render('contacts_portal_type.portal_page_role_customer', values)

    @route(['/factory_representatives'], type='http', auth='user', website=True, readonly=True)
    def portal_factory_reps_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('factory_rep', 'factory_rep')
        values.update({'page_name': 'factory_representatives', 'portal_role_page_title': tenv._('Welcome %s') % label})
        return request.render('contacts_portal_type.portal_page_role_factory_rep', values)

    @route(['/factory_employees'], type='http', auth='user', website=True, readonly=True)
    def portal_factory_employees_home(self, **kw):
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('factory_employee', 'factory_employee')
        values.update({'page_name': 'factory_employees', 'portal_role_page_title': tenv._('Welcome %s') % label})
        return request.render('contacts_portal_type.portal_page_role_factory_employee', values)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if not partner or not partner.portal_contact_type:
            return values
        tenv = self._portal_translation_env()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get(partner.portal_contact_type, partner.portal_contact_type)
        values['portal_contact_welcome'] = tenv._('Welcome %s') % label
        return values
