// ==========================================================================
// SERVICE WORKER - OFFLINE RESOURCE MANAGEMENT
// ==========================================================================

const CACHE_NAME = "sarotoria-static-cache-v1";
const ASSETS_TO_CACHE = [
    "/",
    "/static/css/main.css",
    "/static/js/app.js",
    "/static/js/pwa.js",
    "/static/manifest.json",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
];

// Install Event
self.addEventListener("install", (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log("Sarotoria sw.js: Caching app shells & stylesheets.");
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .then(() => self.skipWaiting())
    );
});

// Activation Event
self.addEventListener("activate", (e) => {
    e.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        console.log("Sarotoria sw.js: Clearing legacy caches.");
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch Event (Cache First falling back to network fetch)
self.addEventListener("fetch", (e) => {
    // Avoid caching POST requests or Supabase dynamic requests
    if (e.request.method !== "GET") {
        return;
    }
    
    e.respondWith(
        caches.match(e.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                return fetch(e.request)
                    .then((networkResponse) => {
                        // Check valid response before caching
                        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== "basic") {
                            return networkResponse;
                        }
                        
                        // Dynamically cache new visual assets or styles
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(e.request, responseToCache);
                            });
                            
                        return networkResponse;
                    })
                    .catch(() => {
                        // Simple offline page fallback or raw error response
                        return new Response("Network connection required for fashion catalog fetch.");
                    });
            })
    );
});
