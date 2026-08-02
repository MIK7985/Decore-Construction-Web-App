const CACHE_NAME = 'decore-cache-v3';
const ASSETS_TO_CACHE = [
  '/dashboard/',
  '/static/css/style.css',
  '/static/images/logo.png',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (!event.request.url.startsWith(self.location.origin) || event.request.method !== 'GET') {
    return;
  }

  // Network-First Strategy:
  event.respondWith(
    fetch(event.request).then(networkResponse => {
      if (event.request.url.includes('/admin/') || event.request.url.includes('browser-sync') || event.request.url.includes('ws/')) {
        return networkResponse;
      }
      if (networkResponse && networkResponse.status === 200) {
        const urlObj = new URL(event.request.url);
        if (urlObj.pathname.startsWith('/static/') || urlObj.pathname === '/dashboard/') {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        }
      }
      return networkResponse;
    }).catch(() => {
      return caches.match(event.request).then(cachedResponse => {
        return cachedResponse || caches.match('/dashboard/');
      });
    })
  );
});
