import { initializeApp } from "https://www.gstatic.com/firebasejs/12.9.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/12.9.0/firebase-analytics.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/12.9.0/firebase-messaging.js";
// Cred will be set as per the cred of mobile dev
  const firebaseConfig = {
//     apiKey: "AIzaSyBdBIbK2e1JDbZGKKXU6yFwL1ze0jprq6Y",
//     authDomain: "asseto-push-notification.firebaseapp.com",
//     projectId: "asseto-push-notification",
//     storageBucket: "asseto-push-notification.firebasestorage.app",
//     messagingSenderId: "600702361358",
//     appId: "1:600702361358:web:58cb3c2ee78e9b1280415f",
//     measurementId: "G-R0J26HTEVL"
      apiKey: 'AIzaSyBiUQoc2jSnM8Et_908_Jcj75RTz1IGgco',
      appId: '1:373301044674:android:e331be3913f69c4518225b',
      messagingSenderId: '373301044674',
      projectId: 'asseto-7f8ee',
      storageBucket: 'asseto-7f8ee.firebasestorage.app',
  };

  const app = initializeApp(firebaseConfig);
  const analytics = getAnalytics(app);

  // Initialize Messaging
  const messaging = getMessaging(app);

  // Request permission and get token
  async function requestPermission() {
    try {
      const permission = await Notification.requestPermission();

      if (permission === "granted") {
        console.log("Notification permission granted.");

        const token = await getToken(messaging, {
        //   vapidKey: "YOUR_PUBLIC_VAPID_KEY"
            vapidKey: "BOaCdMdy3O9TkGYYO5OM3N-CIzAiy83Y34qOa657zhpV928u_dj52Im5HQiSwl32v2UolHtIiegqN3gyB01ycM"
        });

        console.log("FCM Token:", token);
      } else {
        console.log("Permission denied.");
      }
    } catch (error) {
      console.error("Error getting token:", error);
    }
  }

  requestPermission();

  // Optional: Listen for foreground messages
  onMessage(messaging, (payload) => {
    console.log("Message received: ", payload);
  });