/** Hostess portal: shuttle tour actions (geolocation + JSON API). */
(function () {
    function q(sel) {
        return document.querySelector(sel);
    }

    function showStatus(el, msg, ok) {
        if (!el) {
            return;
        }
        el.classList.remove('d-none', 'alert-danger', 'alert-success');
        el.classList.add('border');
        el.classList.add(ok ? 'alert-success' : 'alert-danger');
        el.textContent = msg;
    }

    function getBootstrap() {
        var s = q('#hostess_tour_bootstrap');
        if (!s || !s.textContent) {
            return {};
        }
        try {
            return JSON.parse(s.textContent);
        } catch (e) {
            return {};
        }
    }

    function csrfUrl(path, csrftok) {
        var sep = path.indexOf('?') >= 0 ? '&' : '?';
        return path + sep + 'csrf_token=' + encodeURIComponent(csrftok);
    }

    function getPosition(i18n) {
        i18n = i18n || {};
        return new Promise(function (resolve, reject) {
            if (!navigator.geolocation) {
                reject(
                    new Error(
                        i18n.geolocation_unsupported ||
                            'Geolocation is not supported by this browser.'
                    )
                );
                return;
            }
            navigator.geolocation.getCurrentPosition(
                function (pos) {
                    resolve({
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude,
                    });
                },
                function (err) {
                    reject(err);
                },
                { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
            );
        });
    }

    function postJson(path, csrftok, body, i18n) {
        i18n = i18n || {};
        var url = csrfUrl(path, csrftok);
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
            body: JSON.stringify(body),
        }).then(function (r) {
            return r.text().then(function (text) {
                var ct = (r.headers.get('content-type') || '').toLowerCase();
                var looksJson =
                    ct.indexOf('application/json') >= 0 ||
                    (text && /^\s*\{/.test(text));
                if (looksJson) {
                    try {
                        var data = JSON.parse(text);
                    } catch (e) {
                        throw new Error(
                            i18n.invalid_response_refresh ||
                                'Invalid response from server. Try refreshing the page.'
                        );
                    }
                    if (!r.ok) {
                        var err = (data && data.error) || r.statusText;
                        throw new Error(
                            typeof err === 'string'
                                ? err
                                : i18n.request_failed_generic || 'Request failed'
                        );
                    }
                    return data;
                }
                if (!r.ok) {
                    var failTpl =
                        i18n.request_failed_sign_out ||
                        'Request failed (%s). If the problem continues, sign out and sign in again.';
                    throw new Error(failTpl.replace('%s', String(r.status)));
                }
                throw new Error(
                    i18n.unexpected_non_json ||
                        'Unexpected response from server (not JSON). Try refreshing the page.'
                );            });
        });
    }

    function init() {
        var root = q('#hostess_tour_portal_root');
        if (!root) {
            return;
        }

        var boot = getBootstrap();
        var csrf = boot.csrf || '';
        var L = boot.i18n || {};
        var state = {
            activeTourId: boot.openTour ? boot.openTour.id : null,
            notesTourId: boot.openTour ? boot.openTour.id : null,
        };

        var routeSel = q('#hostess_route_select');
        var shuttleSel = q('#hostess_shuttle_select');
        var statusEl = q('#hostess_tour_status');
        var btnStart = q('#hostess_btn_start');
        var btnAdd = q('#hostess_btn_add_point');
        var btnFinish = q('#hostess_btn_finish');
        var btnNotes = q('#hostess_btn_save_notes');
        var notesInput = q('#hostess_notes_input');

        function filterShuttles() {
            var rid = routeSel.value ? parseInt(routeSel.value, 10) : null;
            var opts = shuttleSel.querySelectorAll('option[value]');
            opts.forEach(function (opt) {
                if (!opt.value) {
                    return;
                }
                var sr = opt.getAttribute('data-route-id');
                var sid = sr ? parseInt(sr, 10) : null;
                var match = !rid || !sid || sid === rid;
                opt.hidden = !match;
            });
            var cur = shuttleSel.options[shuttleSel.selectedIndex];
            if (cur && cur.hidden) {
                shuttleSel.value = '';
            }
        }

        routeSel.addEventListener('change', filterShuttles);
        filterShuttles();

        if (boot.openTour && boot.openTour.route_id) {
            routeSel.value = String(boot.openTour.route_id);
            filterShuttles();
            if (boot.openTour.shuttle_id) {
                shuttleSel.value = String(boot.openTour.shuttle_id);
            }
        }

        function applyTourUi() {
            var active = !!state.activeTourId;
            routeSel.disabled = active;
            shuttleSel.disabled = active;
            btnStart.disabled = active;
            btnAdd.disabled = !active;
            btnFinish.disabled = !active;
            var canNotes = !!(state.activeTourId || state.notesTourId);
            if (notesInput) {
                notesInput.readOnly = !canNotes;
            }
            btnNotes.disabled = !canNotes;
        }

        applyTourUi();

        btnStart.addEventListener('click', function () {
            var routeId = routeSel.value;
            var shuttleId = shuttleSel.value;
            if (!routeId || !shuttleId) {
                showStatus(statusEl, L.select_route_and_shuttle || 'Please select a route and a shuttle.', false);
                return;
            }
            var basePayload = {
                route_id: parseInt(routeId, 10),
                shuttle_id: parseInt(shuttleId, 10),
            };
            showStatus(statusEl, L.getting_location || 'Getting location…', true);
            getPosition(L).then(
                function (coords) {
                    return postJson('/portal/api/hostess/tour/start', csrf, {
                        route_id: basePayload.route_id,
                        shuttle_id: basePayload.shuttle_id,
                        latitude: coords.latitude,
                        longitude: coords.longitude,
                    }, L);
                },
                function () {
                    showStatus(
                        statusEl,
                        L.random_istanbul_fallback ||
                            'No location; using a random point on the Anatolian side of Istanbul.',
                        true
                    );
                    return postJson('/portal/api/hostess/tour/start', csrf, basePayload, L);
                }
            )
                .then(function (data) {
                    state.activeTourId = data.tour_id;
                    state.notesTourId = data.tour_id;
                    if (notesInput) {
                        notesInput.value = '';
                    }
                    var startedTpl = L.tour_started || 'Tour %s started.';
                    showStatus(statusEl, startedTpl.replace('%s', data.tour_no), true);
                    applyTourUi();
                })
                .catch(function (e) {
                    var msg =
                        e && e.message
                            ? e.message
                            : L.could_not_start || 'Could not start tour. Try again.';
                    showStatus(statusEl, msg, false);
                });
        });

        btnAdd.addEventListener('click', function () {
            if (!state.activeTourId) {
                return;
            }
            showStatus(statusEl, L.getting_location || 'Getting location…', true);
            getPosition(L)
                .then(function (coords) {
                    return postJson('/portal/api/hostess/tour/point', csrf, {
                        tour_id: state.activeTourId,
                        latitude: coords.latitude,
                        longitude: coords.longitude,
                    }, L);
                })
                .then(function () {
                    showStatus(statusEl, L.tour_point_added || 'Tour point added.', true);
                })
                .catch(function (e) {
                    showStatus(statusEl, (e && e.message) || L.could_not_add_point || 'Could not add point.', false);
                });
        });

        btnFinish.addEventListener('click', function () {
            if (!state.activeTourId) {
                return;
            }
            showStatus(statusEl, L.getting_location || 'Getting location…', true);
            getPosition(L)
                .then(
                    function (c) {
                        return { latitude: c.latitude, longitude: c.longitude };
                    },
                    function () {
                        return null;
                    }
                )
                .then(function (coords) {
                    var payload = { tour_id: state.activeTourId };
                    if (coords) {
                        payload.latitude = coords.latitude;
                        payload.longitude = coords.longitude;
                    }
                    return postJson('/portal/api/hostess/tour/finish', csrf, payload, L);
                })
                .then(function () {
                    showStatus(statusEl, L.tour_finished || 'Tour finished. Destination recorded.', true);
                    state.activeTourId = null;
                    applyTourUi();
                })
                .catch(function (e) {
                    showStatus(statusEl, (e && e.message) || L.could_not_finish || 'Could not finish tour.', false);
                });
        });

        btnNotes.addEventListener('click', function () {
            var tid = state.activeTourId || state.notesTourId;
            if (!tid || !notesInput) {
                return;
            }
            postJson('/portal/api/hostess/tour/notes', csrf, {
                tour_id: tid,
                notes: notesInput.value,
            }, L)
                .then(function () {
                    showStatus(statusEl, L.notes_saved || 'Notes saved.', true);
                })

                .catch(function (e) {
                    showStatus(statusEl, (e && e.message) || L.could_not_save_notes || 'Could not save notes.', false);
                });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
