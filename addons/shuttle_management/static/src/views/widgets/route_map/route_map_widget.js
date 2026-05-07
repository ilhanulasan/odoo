/** @odoo-module **/

import { loadCSS, loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useRef } from "@odoo/owl";

const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
const LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

/** Anatolian Istanbul: Üsküdar / Kadıköy area (not European side) */
const ISTANBUL_ANATOLIA_CENTER = [41.02, 29.12];
const ISTANBUL_ANATOLIA_ZOOM = 11;

/** OSRM public demo — driving directions along roads (respect usage policy for production). */
const OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving";

export class ShuttleRouteMapWidget extends Component {
    static template = "shuttle_management.RouteMapWidget";
    static props = {
        ...standardWidgetProps,
    };

    setup() {
        this.mapRef = useRef("map");
        this.leafletMap = null;
        this.markersGroup = null;
        this._mapEventsBound = false;
        this._renderGeneration = 0;
        /** Like partner map: frame route once; later redraws must not pan/zoom (e.g. after click-to-add). */
        this._initialViewApplied = false;
        this._boundsRecordKey = undefined;

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
            // Invalidate async refreshMap runs that may resume after await (e.g. OSRM fetch).
            this._renderGeneration++;
            if (this.leafletMap) {
                this.leafletMap.remove();
                this.leafletMap = null;
            }
            this.markersGroup = null;
            this._mapEventsBound = false;
        });
    }

    get mapHelpText() {
        return _t(
            "Click the map to add a point. Drag a pin to move it. With several points, the line follows roads when possible."
        );
    }

    getSortedPointRows() {
        const record = this.props.record;
        const list = record.data.point_ids;
        if (!list || !list.records) {
            return [];
        }
        const rows = [...list.records];
        rows.sort((a, b) => {
            const ds = (a.data.sequence || 0) - (b.data.sequence || 0);
            if (ds !== 0) {
                return ds;
            }
            return String(a.id).localeCompare(String(b.id));
        });
        const out = [];
        for (const rec of rows) {
            const lat = rec.data.latitude;
            const lng = rec.data.longitude;
            if (lat == null || lng == null) {
                continue;
            }
            if (Number.isNaN(lat) || Number.isNaN(lng)) {
                continue;
            }
            out.push({
                record: rec,
                lat,
                lng,
                label: rec.data.name || "",
                address: rec.data.address || "",
            });
        }
        return out;
    }

    async fetchOsrmDrivingGeometry(latlngs) {
        if (!latlngs || latlngs.length < 2) {
            return null;
        }
        const coordStr = latlngs.map(([lat, lng]) => `${lng},${lat}`).join(";");
        const url = `${OSRM_ROUTE_URL}/${coordStr}?overview=full&geometries=geojson`;
        try {
            const res = await fetch(url);
            const data = await res.json();
            if (data.code !== "Ok" || !data.routes?.[0]?.geometry?.coordinates) {
                return null;
            }
            const coords = data.routes[0].geometry.coordinates;
            return coords.map(([lng, lat]) => [lat, lng]);
        } catch {
            return null;
        }
    }

    bindMapEvents() {
        if (this._mapEventsBound || !this.leafletMap) {
            return;
        }
        this._mapEventsBound = true;
        this.leafletMap.on("click", (e) => {
            void this.onMapClick(e);
        });
    }

    async onMapClick(e) {
        if (this.props.readonly) {
            return;
        }
        const list = this.props.record.data.point_ids;
        if (!list || typeof list.addNewRecord !== "function") {
            return;
        }
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        const maxSeq = list.records.length
            ? Math.max(...list.records.map((r) => r.data.sequence || 0))
            : 0;
        const rec = await list.addNewRecord({ position: "bottom" });
        await rec.update({
            latitude: lat,
            longitude: lng,
            sequence: maxSeq + 10,
        });
    }

    async refreshMap() {
        const L = globalThis.L;
        const el = this.mapRef.el;
        if (!L || !el) {
            return;
        }
        const recordKey = this.props.record.resId ?? this.props.record.id;
        if (this._boundsRecordKey !== recordKey) {
            this._boundsRecordKey = recordKey;
            this._initialViewApplied = false;
        }

        const generation = ++this._renderGeneration;

        if (!this.leafletMap) {
            this.leafletMap = L.map(el, { scrollWheelZoom: true, zoomControl: true });
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors",
            }).addTo(this.leafletMap);
            this.markersGroup = L.featureGroup().addTo(this.leafletMap);
            this.bindMapEvents();
        } else {
            this.markersGroup.clearLayers();
        }

        const Lref = L;
        const pointRows = this.getSortedPointRows();
        const latlngs = pointRows.map((p) => [p.lat, p.lng]);

        let routeLatLngs = null;
        if (latlngs.length >= 2) {
            routeLatLngs = await this.fetchOsrmDrivingGeometry(latlngs);
        }
        if (generation !== this._renderGeneration || !this.leafletMap || !this.markersGroup) {
            return;
        }

        if (routeLatLngs?.length) {
            Lref.polyline(routeLatLngs, { color: "#714B67", weight: 5, opacity: 0.92 }).addTo(
                this.markersGroup
            );
        } else if (latlngs.length > 1) {
            Lref.polyline(latlngs, {
                color: "#9d7899",
                weight: 3,
                opacity: 0.65,
                dashArray: "10 8",
            }).addTo(this.markersGroup);
        }

        const readonly = this.props.readonly;
        pointRows.forEach((p, index) => {
            const parts = [];
            if (p.label) {
                parts.push(p.label);
            }
            if (p.address) {
                parts.push(p.address);
            }
            const popupText = parts.length ? parts.join("\n") : `#${index + 1}`;
            const m = Lref.marker([p.lat, p.lng], { draggable: !readonly });
            m.bindPopup(String(popupText));
            m.addTo(this.markersGroup);
            if (!readonly) {
                m.on("dragend", () => {
                    const ll = m.getLatLng();
                    p.record.update({ latitude: ll.lat, longitude: ll.lng });
                });
            }
        });

        if (generation !== this._renderGeneration || !this.leafletMap) {
            return;
        }

        if (!this._initialViewApplied) {
            this._initialViewApplied = true;
            if (latlngs.length) {
                if (routeLatLngs?.length) {
                    this.leafletMap.fitBounds(Lref.latLngBounds(routeLatLngs), {
                        padding: [32, 32],
                        maxZoom: 16,
                    });
                } else {
                    this.leafletMap.fitBounds(Lref.latLngBounds(latlngs), {
                        padding: [32, 32],
                        maxZoom: 16,
                    });
                }
            } else {
                this.leafletMap.setView(ISTANBUL_ANATOLIA_CENTER, ISTANBUL_ANATOLIA_ZOOM);
            }
        }
    }
}

export const shuttleRouteMapWidget = {
    component: ShuttleRouteMapWidget,
    fieldDependencies: [
        { name: "point_ids", type: "one2many" },
    ],
};

registry.category("view_widgets").add("shuttle_route_map", shuttleRouteMapWidget);
