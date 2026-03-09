/* eslint-disable no-restricted-globals */
import { precacheAndRoute } from "workbox-precaching";

precacheAndRoute(self.__WB_MANIFEST || []);

const APP_SHELL_CACHE = "clipai-app-shell-v1";
const API_CACHE = "clipai-api-v1";
const CLIP_CACHE = "clipai-clips-v1";
const QUEUE_CACHE = "clipai-queue-v1";
const OFFLINE_URL = "/offline.html";

const APP_SHELL_ASSETS = ["/", OFFLINE_URL, "/manifest.json"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(APP_SHELL_CACHE).then((cache) => cache.addAll(APP_SHELL_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => ![APP_SHELL_CACHE, API_CACHE, CLIP_CACHE, QUEUE_CACHE].includes(key))
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
    return response;
  } catch (_err) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    if (request.mode === "navigate") {
      return caches.match(OFFLINE_URL);
    }
    return new Response(JSON.stringify({ detail: "offline" }), {
      status: 503,
      headers: { "Content-Type": "application/json" }
    });
  }
}

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  const response = await fetch(request);
  const cache = await caches.open(cacheName);
  cache.put(request, response.clone());
  return response;
}

function isApiRequest(url) {
  return url.pathname.startsWith("/auth") ||
    url.pathname.startsWith("/video") ||
    url.pathname.startsWith("/clips") ||
    url.pathname.startsWith("/payment") ||
    url.pathname.startsWith("/notifications");
}

function isClipAsset(url) {
  return url.pathname.includes("/media/") || /\.(mp4|webm|mov)$/i.test(url.pathname);
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method === "GET" && request.mode === "navigate") {
    event.respondWith(networkFirst(request, APP_SHELL_CACHE));
    return;
  }

  if (request.method === "GET" && isApiRequest(url)) {
    event.respondWith(networkFirst(request, API_CACHE));
    return;
  }

  if (request.method === "GET" && isClipAsset(url)) {
    event.respondWith(cacheFirst(request, CLIP_CACHE));
    return;
  }

  if (request.method === "GET" && url.origin === self.location.origin) {
    event.respondWith(cacheFirst(request, APP_SHELL_CACHE));
  }
});

async function queueYoutubeJob(payload) {
  const cache = await caches.open(QUEUE_CACHE);
  const key = new Request(`/__queue__/${Date.now()}`);
  const response = new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" }
  });
  await cache.put(key, response);
}

async function flushQueue() {
  const cache = await caches.open(QUEUE_CACHE);
  const keys = await cache.keys();

  for (const key of keys) {
    const response = await cache.match(key);
    if (!response) {
      continue;
    }
    try {
      const payload = await response.json();
      await fetch("/video/process", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: payload.authorization || ""
        },
        body: JSON.stringify({ youtube_url: payload.youtube_url })
      });
      await cache.delete(key);
    } catch (_err) {
      // keep request for next sync
    }
  }
}

self.addEventListener("message", (event) => {
  if (!event.data) {
    return;
  }
  if (event.data.type === "QUEUE_YOUTUBE_LINK") {
    event.waitUntil(queueYoutubeJob(event.data.payload));
  }
  if (event.data.type === "FLUSH_QUEUE") {
    event.waitUntil(flushQueue());
  }
});

self.addEventListener("sync", (event) => {
  if (event.tag === "clipai-sync-jobs") {
    event.waitUntil(flushQueue());
  }
});

self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || "ClipAI";
  const options = {
    body: data.body || "Tes clips sont prets.",
    icon: "/icons/icon-192.png",
    badge: "/icons/icon-96.png",
    data: { url: data.url || "/dashboard" }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || "/dashboard";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if ("focus" in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      return clients.openWindow(targetUrl);
    })
  );
});
