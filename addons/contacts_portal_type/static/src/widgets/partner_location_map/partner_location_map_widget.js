import { loadCSS, loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useRef } from "@odoo/owl";

const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
const LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

// İstanbul (Anatolian side) default
const DEFAULT_CENTER = [41.02, 29.12];
const DEFAULT_ZOOM = 11;

const MANUAL_PIN_GRACE_MS = 2500;

function makePartnerAddress(data) {
    const parts = [];
    if (data.street) parts.push(data.street);
    if (data.street2) parts.push(data.street2);
    if (data.zip) parts.push(data.zip);
    if (data.city) parts.push(data.city);
    if (data.state_id?.[1]) parts.push(data.state_id[1]);
    if (data.country_id?.[1]) parts.push(data.country_id[1]);
    return parts.join(", ");
}

export class PartnerLocationMapWidget extends Component {
    static template = "contacts_portal_type.PartnerLocationMapWidget";
    static props = {
        ...standardWidgetProps,
    };

    setup() {
        this.mapRef = useRef("map");
        this.leafletMap = null;
        this.marker = null;
        this._mapEventsBound = false;
        this._renderGeneration = 0;
        this._lastGeocodeQuery = "";
        this._geocodeTimer = null;
        this._suppressAddressGeocodeUntil = 0;
        this._lastManualLatLng = null;

        onWillStart(async () => {
            await Promise.all([loadCSS(LEAFLET_CSS), loadJS(LEAFLET_JS)]);
        });
        onMounted(() => {
            void this.refreshMap();
        });
        onPatched(() => {
            void this.refreshMap();
        });
        onWillUnmount(() => {
            if (this._geocodeTimer) {
                clearTimeout(this._geocodeTimer);
                this._geocodeTimer = null;
            }
            if (this.leafletMap) {
                this.leafletMap.remove();
                this.leafletMap = null;
            }
        });
    }

    get helpText() {
        if (this.props.readonly) {
            return _t("Location (read-only).");
        }
        return _t("Click the map to set the location. Drag the pin to fine-tune. Editing the address will update the pin.");
    }

    getLatLng() {
        const { partner_latitude: lat, partner_longitude: lng } = this.props.record.data;
        if (lat == null || lng == null) return null;
        if (Number.isNaN(lat) || Number.isNaN(lng)) return null;
        if (lat === 0 && lng === 0) return null;
        return [lat, lng];
    }

    bindMapEvents() {
        if (this._mapEventsBound || !this.leafletMap) return;
        this._mapEventsBound = true;
        this.leafletMap.on("click", (e) => void this.onMapClick(e));
    }

    async onMapClick(e) {
        if (this.props.readonly) return;
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        this._lastManualLatLng = [lat, lng];
        await this.props.record.update({
            partner_latitude: lat,
            partner_longitude: lng,
        });
        // Don't let the reverse-geocoded address trigger a geocode that recenters the pin.
        this._suppressAddressGeocodeUntil = Date.now() + MANUAL_PIN_GRACE_MS;
        try {
            await this.reverseGeocodeAndFillAddress(lat, lng);
        } finally {
            // keep suppression single-shot (scheduleGeocodeFromAddress resets it)
        }
    }

    scheduleGeocodeFromAddress() {
        if (this.props.readonly) return;
        if (Date.now() < this._suppressAddressGeocodeUntil) {
            return;
        }
        const data = this.props.record.data;
        const query = makePartnerAddress(data);
        if (!query || query.length < 6) return;
        if (query === this._lastGeocodeQuery) return;

        this._lastGeocodeQuery = query;
        if (this._geocodeTimer) {
            clearTimeout(this._geocodeTimer);
        }
        this._geocodeTimer = setTimeout(() => {
            this._geocodeTimer = null;
            void this.geocodeAddressAndMovePin(query);
        }, 600);
    }

    async geocodeAddressAndMovePin(query) {
        try {
            const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(
                query
            )}`;
            const res = await fetch(url, { headers: { "Accept-Language": "tr" } });
            const data = await res.json();
            if (!Array.isArray(data) || !data.length) return;
            const lat = Number.parseFloat(data[0].lat);
            const lng = Number.parseFloat(data[0].lon);
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
            // If the user has just pinned a precise location, don't overwrite it
            // with a coarse geocode result (often street center).
            if (Date.now() < this._suppressAddressGeocodeUntil && this._lastManualLatLng) {
                return;
            }
            await this.props.record.update({
                partner_latitude: lat,
                partner_longitude: lng,
            });
            // Ensure country/address are also filled when geocoding from typed address.
            await this.reverseGeocodeAndFillAddress(lat, lng);
        } catch {
            // ignore network/geocode errors
        }
    }

    async reverseGeocodeAndFillAddress(lat, lng) {
        try {
            const url = `https://nominatim.openstreetmap.org/reverse?format=json&zoom=18&addressdetails=1&lat=${encodeURIComponent(
                String(lat)
            )}&lon=${encodeURIComponent(String(lng))}`;
            const res = await fetch(url, { headers: { "Accept-Language": "tr" } });
            const data = await res.json();
            const a = data?.address || {};

            const street = [a.road, a.house_number].filter(Boolean).join(" ").trim();
            // Mapping for TR:
            // - Odoo `city` should be town/district (ilçe)
            // - Odoo `state_id` should be province/city (il)
            const city =
                a.town ||
                a.city_district ||
                a.municipality ||
                a.county ||
                a.village ||
                "";
            const stateName = a.city || a.state || a.province || a.region || "";
            const zip = a.postcode || "";
            const countryCode = (a.country_code || "").toUpperCase();

            const updateVals = {};
            if (street) updateVals.street = street;
            if (city) updateVals.city = city;
            if (zip) updateVals.zip = zip;

            // Apply simple char fields first (so they don't get blocked by a relational update).
            if (Object.keys(updateVals).length) {
                await this.props.record.update(updateVals);
            }

            // Many2one values must be `{id, display_name}` in the web client model layer.
            if (countryCode) {
                const orm = this.env.services.orm;
                const countries = await orm.searchRead(
                    "res.country",
                    [["code", "=", countryCode]],
                    ["display_name", "name"],
                    { limit: 1 }
                );
                const c = countries?.[0];
                if (c?.id) {
                    await this.props.record.update({
                        country_id: { id: c.id, display_name: c.display_name || c.name },
                    });
                    // Fill state based on country + stateName when available.
                    if (stateName) {
                        const states = await orm.searchRead(
                            "res.country.state",
                            [
                                ["country_id", "=", c.id],
                                ["name", "ilike", stateName],
                            ],
                            ["display_name", "name"],
                            { limit: 1 }
                        );
                        const s = states?.[0];
                        if (s?.id) {
                            await this.props.record.update({
                                state_id: { id: s.id, display_name: s.display_name || s.name },
                            });
                        }
                    }
                }
            }
        } catch {
            // ignore network/reverse-geocode errors
        }
    }

    async refreshMap() {
        const L = globalThis.L;
        const el = this.mapRef.el;
        if (!L || !el) return;

        const generation = ++this._renderGeneration;
        const isNewMap = !this.leafletMap;
        if (!this.leafletMap) {
            this.leafletMap = L.map(el, { scrollWheelZoom: true, zoomControl: true });
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors",
            }).addTo(this.leafletMap);
            this.bindMapEvents();
        }

        const ll = this.getLatLng();
        if (ll) {
            const readonly = this.props.readonly;
            if (!this.marker) {
                this.marker = L.marker(ll, { draggable: !readonly }).addTo(this.leafletMap);
                if (!readonly) {
                    this.marker.on("dragend", async () => {
                        const pos = this.marker.getLatLng();
                        this._lastManualLatLng = [pos.lat, pos.lng];
                        await this.props.record.update({
                            partner_latitude: pos.lat,
                            partner_longitude: pos.lng,
                        });
                        // Don't let the reverse-geocoded address trigger a geocode that recenters the pin.
                        this._suppressAddressGeocodeUntil = Date.now() + MANUAL_PIN_GRACE_MS;
                        try {
                            await this.reverseGeocodeAndFillAddress(pos.lat, pos.lng);
                        } finally {
                            // keep suppression single-shot (scheduleGeocodeFromAddress resets it)
                        }
                    });
                }
            } else {
                // Update pin without moving the map (no pan/center on pin updates).
                this.marker.setLatLng(ll);
                if (this.marker.dragging) {
                    readonly ? this.marker.dragging.disable() : this.marker.dragging.enable();
                }
            }
            // Only apply a zoom/center on the first render.
            if (isNewMap) this.leafletMap.setView(ll, 16);
        } else {
            if (this.marker) {
                this.marker.remove();
                this.marker = null;
            }
            this.leafletMap.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
        }

        if (generation !== this._renderGeneration) return;
        this.scheduleGeocodeFromAddress();
    }
}

export const partnerLocationMapWidget = {
    component: PartnerLocationMapWidget,
    fieldDependencies: [
        { name: "partner_latitude", type: "float" },
        { name: "partner_longitude", type: "float" },
        { name: "street", type: "char" },
        { name: "street2", type: "char" },
        { name: "zip", type: "char" },
        { name: "city", type: "char" },
        { name: "state_id", type: "many2one" },
        { name: "country_id", type: "many2one" },
    ],
};

registry.category("view_widgets").add("partner_location_map", partnerLocationMapWidget);
