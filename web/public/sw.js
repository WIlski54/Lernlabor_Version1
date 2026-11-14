// Hält die Welt-Dateien nach dem ersten Laden auf dem Gerät (Cache zuerst), alles andere Netz zuerst.
// Der Cache-Name enthält einen Hash über public/welt (setzt tools/optimieren.mjs) – neue Welt → neuer Cache.
const CACHE = 'garten-labor-welt-bfc6c3c372';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((namen) => Promise.all(namen.filter((n) => n !== CACHE).map((n) => caches.delete(n)))));
  self.clients.claim();
});

/** Nur vollständige Dateien ablegen – nie eine HTML-Fehler-/Fallbackseite unter /welt/. */
function cachebar(antwort) {
  return antwort.status === 200 && !(antwort.headers.get('content-type') || '').includes('text/html');
}

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || !url.pathname.startsWith('/welt/')) return;
  let ablegen = Promise.resolve();
  const antwort = caches.open(CACHE).then(async (c) => {
    const treffer = await c.match(e.request);
    if (treffer) return treffer;
    // no-cache: am HTTP-Cache vorbei (ETag-Revalidierung), damit kein veralteter Stand im neuen Cache landet
    const netz = await fetch(e.request, { cache: 'no-cache' });
    if (cachebar(netz)) ablegen = c.put(e.request, netz.clone());
    return netz;
  });
  e.respondWith(antwort);
  e.waitUntil(antwort.then(() => ablegen).catch(() => {}));
});
