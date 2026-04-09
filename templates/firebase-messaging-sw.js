importScripts("https://www.gstatic.com/firebasejs/12.9.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/12.9.0/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyBdBIbK2e1JDbZGKKXU6yFwL1ze0jprq6Y",
  authDomain: "asseto-push-notification.firebaseapp.com",
  projectId: "asseto-push-notification",
  messagingSenderId: "600702361358",
  appId: "1:600702361358:web:58cb3c2ee78e9b1280415f"
});

firebase.messaging();
