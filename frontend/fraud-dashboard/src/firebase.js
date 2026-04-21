// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyD51sR8Q_N8YXRl53v1Q-PCTXNv39dJd7Q",
  authDomain: "capstone-ea711.firebaseapp.com",
  projectId: "capstone-ea711",
  storageBucket: "capstone-ea711.firebasestorage.app",
  messagingSenderId: "674836872879",
  appId: "1:674836872879:web:83266d4e6d88ee1a4bde5a",
  measurementId: "G-DJPTDQCGVD"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
