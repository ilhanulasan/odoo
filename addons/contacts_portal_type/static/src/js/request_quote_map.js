/* global L */

(function () {
    "use strict";

    const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    const LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    const DEFAULT_CENTER = [41.02, 29.12];
    const DEFAULT_ZOOM = 11;

    function loadCSS(href) {
        return new Promise(function (resolve, reject) {
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = href;
            link.onload = function () {
                resolve();
            };
            link.onerror = function () {
                reject(new Error("Failed to load CSS: " + href));
            };
            document.head.appendChild(link);
        });
    }

    function loadJS(src) {
        return new Promise(function (resolve, reject) {
            const script = document.createElement("script");
            script.src = src;
            script.async = true;
            script.onload = function () {
                resolve();
            };
            script.onerror = function () {
                reject(new Error("Failed to load script: " + src));
            };
            document.head.appendChild(script);
        });
    }

    function parseHiddenFloat(el) {
        if (!el || !el.value) {
            return null;
        }
        const n = parseFloat(el.value);
        return Number.isFinite(n) ? n : null;
    }

    async function reverseGeocodeFillAddress(lat, lng, streetEl, zipEl, cityEl) {
        if (!streetEl && !zipEl && !cityEl) {
            return;
        }
        try {
            const url =
                "https://nominatim.openstreetmap.org/reverse?format=json&zoom=18&addressdetails=1&lat=" +
                encodeURIComponent(String(lat)) +
                "&lon=" +
                encodeURIComponent(String(lng));
            const res = await fetch(url, { headers: { "Accept-Language": "tr" } });
            const data = await res.json();
            const a = data && data.address ? data.address : {};
            const street = [a.road, a.house_number].filter(Boolean).join(" ").trim();
            if (streetEl && streetEl.value.trim() === "" && street) {
                streetEl.value = street;
            }
            const city =
                a.town ||
                a.city_district ||
                a.municipality ||
                a.county ||
                a.village ||
                a.city ||
                "";
            if (cityEl && cityEl.value.trim() === "" && city) {
                cityEl.value = city;
            }
            const zip = a.postcode || "";
            if (zipEl && zipEl.value.trim() === "" && zip) {
                zipEl.value = zip;
            }
        } catch {
            /* ignore */
        }
    }

    async function initMap() {
        const el = document.getElementById("o_request_quote_map");
        if (!el || el.dataset.leafletInit === "1") {
            return;
        }
        el.dataset.leafletInit = "1";

        const latInput = document.getElementById("o_request_quote_lat");
        const lngInput = document.getElementById("o_request_quote_lng");
        const streetInput = document.querySelector(".o_request_quote_street");
        const zipInput = document.querySelector(".o_request_quote_zip");
        const cityInput = document.querySelector(".o_request_quote_city");

        await Promise.all([loadCSS(LEAFLET_CSS), loadJS(LEAFLET_JS)]);

        const Lref = window.L;
        if (!Lref) {
            return;
        }

        const map = Lref.map(el, { scrollWheelZoom: true, zoomControl: true });
        Lref.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors",
        }).addTo(map);

        let marker = null;

        function setPin(lat, lng, skipReverse) {
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                return;
            }
            if (latInput) {
                latInput.value = String(lat);
            }
            if (lngInput) {
                lngInput.value = String(lng);
            }
            if (!marker) {
                marker = Lref.marker([lat, lng], { draggable: true }).addTo(map);
                marker.on("dragend", function () {
                    const p = marker.getLatLng();
                    void reverseGeocodeFillAddress(p.lat, p.lng, streetInput, zipInput, cityInput);
                });
            } else {
                marker.setLatLng([lat, lng]);
            }
            map.setView([lat, lng], 16);
            if (!skipReverse) {
                void reverseGeocodeFillAddress(lat, lng, streetInput, zipInput, cityInput);
            }
        }

        const existingLat = parseHiddenFloat(latInput);
        const existingLng = parseHiddenFloat(lngInput);
        if (existingLat !== null && existingLng !== null) {
            setPin(existingLat, existingLng, true);
        } else {
            map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
        }

        map.on("click", function (e) {
            setPin(e.latlng.lat, e.latlng.lng, false);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            void initMap();
        });
    } else {
        void initMap();
    }
})();
