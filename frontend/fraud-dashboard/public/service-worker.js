/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'fraudshield-v3';

// Only cache static assets — NEVER cache API responses
const urlsToCache = [
  './',
  'index.html',
  'logo192.png',
  'logo512.png',
  'manifest.json',
];

// Install — cache app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[FraudShield SW] Caching app shell');
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting();
});

// Activate — delete ALL old caches to force fresh content
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[FraudShield SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      )
    )
  );
  self.clients.claim();
});

// Fetch handler — network-only for API, network-first for static assets
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET requests entirely
  if (event.request.method !== 'GET') return;

  // NEVER cache API requests (Render backend, localhost, or any API calls)
  if (
    url.hostname.includes('onrender.com') ||
    url.hostname === 'localhost' ||
    url.pathname.startsWith('/investigate') ||
    url.pathname.startsWith('/summary') ||
    url.pathname.startsWith('/alerts') ||
    url.pathname.startsWith('/spam') ||
    url.pathname.startsWith('/account') ||
    url.pathname.startsWith('/network') ||
    url.pathname.startsWith('/shap') ||
    url.pathname.startsWith('/run') ||
    url.pathname.startsWith('/api')
  ) {
    // Network-only for API — no caching at all
    return;
  }

  // For static assets: network first, fallback to cache
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Only cache successful responses for same-origin static files
        if (response.ok && url.origin === self.location.origin) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline fallback to cache
        return caches.match(event.request);
      })
  );
});
