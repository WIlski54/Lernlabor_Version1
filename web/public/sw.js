// Hält die Welt-Dateien nach dem ersten Laden auf dem Gerät (Cache zuerst), alles andere Netz zuerst.
const CACHE = 'garten-labor-welt-v1';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((namen) => Promise.all(namen.filter((n) => n !== CACHE).map((n) => caches.delete(n)))));
  self.clients.claim();
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.startsWith('/welt/')) {
    e.respondWith(caches.open(CACHE).then(async (c) => {
      const treffer = await c.match(e.request);
      if (treffer) return treffer;
      const antwort = await fetch(e.request);
      if (antwort.ok) c.put(e.request, antwort.clone());
      return antwort;
    }));
  }
});
