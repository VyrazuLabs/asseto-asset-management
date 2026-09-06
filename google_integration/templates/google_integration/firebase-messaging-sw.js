import { initializeApp } from "https://www.gstatic.com/firebasejs/12.9.0/firebase-app.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/12.9.0/firebase-messaging.js";

// Rendered server-side from GoogleCloudFirebaseConfig — no hardcoded project
// values in this file. If Google Cloud hasn't been connected yet (Settings >
// Extensions > Firebase), every field below is empty and initializeApp() is
// skipped so this doesn't throw for installs that haven't provisioned yet.
const firebaseConfig = {{ web_config_json|safe }};
const vapidKey = {{ vapid_key_json|safe }};

if (firebaseConfig.apiKey) {
  const app = initializeApp(firebaseConfig);
  const messaging = getMessaging(app);

  async function requestPermission() {
    try {
      const permission = await Notification.requestPermission();
      if (permission === "granted" && vapidKey) {
        await getToken(messaging, { vapidKey });
      }
    } catch (error) {
      console.error("Error getting FCM token:", error);
    }
  }

  requestPermission();

  onMessage(messaging, (payload) => {
    console.log("Message received: ", payload);
  });
}
