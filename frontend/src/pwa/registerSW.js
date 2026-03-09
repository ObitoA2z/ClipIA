export function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return;
  }

  window.addEventListener("load", async () => {
    try {
      const registration = await navigator.serviceWorker.register("/sw.js", { scope: "/" });

      if (registration?.sync) {
        try {
          await registration.sync.register("clipai-sync-jobs");
        } catch {
          // Background Sync may be unavailable on some browsers.
        }
      }
    } catch {
      // keep silent in production UI, backend logs remain source of truth.
    }
  });
}

export async function askNotificationPermission() {
  if (!("Notification" in window) || !("serviceWorker" in navigator)) {
    return "unsupported";
  }
  if (Notification.permission === "granted") {
    return "granted";
  }
  return Notification.requestPermission();
}
