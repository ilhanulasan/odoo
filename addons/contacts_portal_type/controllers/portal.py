# -*- coding: utf-8 -*-
from odoo.http import request, route
from odoo.tools.translate import LazyTranslate

from odoo.addons.portal.controllers.portal import CustomerPortal

_lt = LazyTranslate(__name__)


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
                    'hostess': '/hostess',
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
        values.update(
            {
                'page_name': 'parents2',
                'portal_role_page_title': tenv._('Parents'),
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
        values = self._prepare_portal_layout_values()
        tenv = self._portal_translation_env()
        partner_fields = tenv['res.partner'].fields_get(['portal_contact_type'])
        selection = partner_fields.get('portal_contact_type', {}).get('selection') or []
        labels = dict(selection)
        label = labels.get('hostess', 'hostess')
        values.update({'page_name': 'hostess', 'portal_role_page_title': tenv._('Welcome %s') % label})
        return request.render('contacts_portal_type.portal_page_role_hostess', values)

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
