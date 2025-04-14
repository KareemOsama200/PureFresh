// OpenStreetMap initialization for location selection
let map;
let marker;

// Initialize map on the registration or checkout page
function initMap() {
    // Default location (Cairo, Egypt)
    const defaultLocation = [31.2357, 30.0444]; // Note: Leaflet uses [lng, lat] format
    
    // Get the map container
    const mapElement = document.getElementById('map');
    
    if (!mapElement) return;
    
    // Check for existing coordinates (for edit forms)
    const latInput = document.getElementById('location_lat');
    const lngInput = document.getElementById('location_lng');
    
    let startPosition = defaultLocation;
    
    if (latInput && latInput.value && lngInput && lngInput.value) {
        startPosition = [
            parseFloat(lngInput.value),
            parseFloat(latInput.value)
        ];
    }
    
    // Initialize map
    map = L.map(mapElement).setView([startPosition[1], startPosition[0]], 13);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Add a marker for the selected location
    marker = L.marker([startPosition[1], startPosition[0]], {
        draggable: true
    }).addTo(map);
    
    // Update coordinates when marker is dragged
    marker.on('dragend', function() {
        const position = marker.getLatLng();
        updateLocationInputs(position.lat, position.lng);
    });
    
    // Allow clicking on map to place marker
    map.on('click', function(event) {
        marker.setLatLng(event.latlng);
        updateLocationInputs(event.latlng.lat, event.latlng.lng);
    });
    
    // Try to get user's current location if allowed
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                map.setView([pos.lat, pos.lng], 15);
                marker.setLatLng([pos.lat, pos.lng]);
                updateLocationInputs(pos.lat, pos.lng);
            },
            function() {
                // User denied geolocation or it failed
                console.log("Geolocation failed");
            }
        );
    }
}

// Update hidden form inputs with selected coordinates
function updateLocationInputs(lat, lng) {
    const latInput = document.getElementById('location_lat');
    const lngInput = document.getElementById('location_lng');
    
    if (latInput && lngInput) {
        latInput.value = lat;
        lngInput.value = lng;
    }
}

// Initialize tracking map for order details page
function initTrackingMap() {
    const trackingMapElement = document.getElementById('tracking-map');
    
    if (!trackingMapElement) return;
    
    const lat = parseFloat(trackingMapElement.dataset.lat);
    const lng = parseFloat(trackingMapElement.dataset.lng);
    
    if (isNaN(lat) || isNaN(lng)) {
        // Handle missing coordinates
        trackingMapElement.innerHTML = '<div class="alert alert-warning">لا توجد إحداثيات موقع لهذا الطلب</div>';
        return;
    }
    
    // Initialize map
    const trackingMap = L.map(trackingMapElement).setView([lat, lng], 15);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(trackingMap);
    
    // Add a marker for the delivery location
    L.marker([lat, lng], {
        title: 'موقع التوصيل'
    }).addTo(trackingMap);
}

// Load Leaflet CSS and JS files
function loadMapDependencies() {
    const mapElement = document.getElementById('map');
    const trackingMapElement = document.getElementById('tracking-map');
    
    if (!mapElement && !trackingMapElement) return;

    // Add Leaflet CSS
    const leafletCSS = document.createElement('link');
    leafletCSS.rel = 'stylesheet';
    leafletCSS.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    leafletCSS.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
    leafletCSS.crossOrigin = '';
    document.head.appendChild(leafletCSS);
    
    // Add Leaflet JS
    const leafletJS = document.createElement('script');
    leafletJS.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    leafletJS.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
    leafletJS.crossOrigin = '';
    document.head.appendChild(leafletJS);
    
    // Init maps after Leaflet is loaded
    leafletJS.onload = function() {
        if (mapElement) {
            initMap();
        } else if (trackingMapElement) {
            initTrackingMap();
        }
    };
}

// Initialize maps when the DOM is loaded
document.addEventListener('DOMContentLoaded', loadMapDependencies);
