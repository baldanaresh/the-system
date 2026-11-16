/* THE SYSTEM - service worker: makes the app installable and usable offline.
   Bump CACHE when you change which files are cached. */
const CACHE = 'the-system-v1';
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png'];
const CDN = ['cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).catch(() => { }).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const url = new URL(req.url), same = url.origin === location.origin;
  // live data is never cached: helper API, the job's data file, and third-party APIs
  if (same && (url.pathname.includes('/api/') || url.pathname.includes('/data/'))) return;
  if (!same && !CDN.includes(url.hostname)) return;
  const put = res => { if (res && (res.ok || res.type === 'opaque')) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); } return res; };
  if (same && (req.mode === 'navigate' || url.pathname.endsWith('/') || url.pathname.endsWith('index.html'))) {
    // the page itself: network first so updates arrive, cache as offline fallback
    e.respondWith(fetch(req).then(put).catch(() => caches.match(req).then(r => r || caches.match('index.html'))));
    return;
  }
  // libraries, fonts, icons: cache first
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(put)));
});
