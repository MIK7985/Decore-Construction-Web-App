/* =========================================================
   Decore PWA Service Worker  v5
   Strategy:
     - Shell (CSS/JS/fonts): Cache-First — instant loads
     - HTML pages: Network-First with cache fallback — fresh data
     - Images: Cache-First with 30-day expiry
     - API/AJAX (JSON): Network-Only — never stale
   ========================================================= */
"use strict";

const SW_VERSION = 'decore-v6';
const SHELL_CACHE  = `${SW_VERSION}-shell`;
const PAGE_CACHE   = `${SW_VERSION}-pages`;
const IMAGE_CACHE  = `${SW_VERSION}-images`;

// Static assets to pre-cache on install (app shell)
const SHELL_ASSETS = [
  '/static/css/style.css',
  '/static/js/app.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
];

// ── Install: pre-cache the app shell ──────────────────────────────────────────
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(SHELL_CACHE).then(cache => cache.addAll(SHELL_ASSETS).catch(() => {}))
  );
});

// ── Activate: prune old caches ─────────────────────────────────────────────────
self.addEventListener('activate', event => {
  const allowed = [SHELL_CACHE, PAGE_CACHE, IMAGE_CACHE];
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => !allowed.includes(k)).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: apply strategy by request type ──────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET, cross-origin (except CDN), chrome-extension
  if (request.method !== 'GET') return;
  if (url.protocol === 'chrome-extension:') return;

  // Never cache API / AJAX JSON responses
  const acceptHeader = request.headers.get('Accept') || '';
  if (acceptHeader.includes('application/json') || url.pathname.startsWith('/api/')) return;

  // Images → Cache-First (30 days)
  if (request.destination === 'image') {
    event.respondWith(cacheFirst(request, IMAGE_CACHE, 60 * 60 * 24 * 30));
    return;
  }

  // CSS / JS / Fonts → Cache-First (shell)
  if (
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'font' ||
    url.hostname === 'cdn.jsdelivr.net' ||
    url.hostname === 'fonts.googleapis.com' ||
    url.hostname === 'fonts.gstatic.com'
  ) {
    event.respondWith(cacheFirst(request, SHELL_CACHE));
    return;
  }

  // HTML pages → Network-First with cache fallback
  if (request.destination === 'document' || acceptHeader.includes('text/html')) {
    event.respondWith(networkFirst(request, PAGE_CACHE));
    return;
  }
});

// ── Strategy helpers ───────────────────────────────────────────────────────────
async function cacheFirst(request, cacheName, maxAgeSeconds = null) {
  const cache  = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) {
    // Check max-age if set
    if (maxAgeSeconds) {
      const dateHeader = cached.headers.get('date');
      if (dateHeader) {
        const age = (Date.now() - new Date(dateHeader).getTime()) / 1000;
        if (age > maxAgeSeconds) {
          return fetchAndCache(request, cache);
        }
      }
    }
    return cached;
  }
  return fetchAndCache(request, cache);
}

async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await cache.match(request);
    return cached || new Response('<h1>Offline</h1><p>Please check your connection.</p>', {
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

async function fetchAndCache(request, cache) {
  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('', { status: 408 });
  }
}
