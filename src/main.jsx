import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

console.log("🚀 React is starting inside Telegram WebApp...");

const rootElement = document.getElementById('root');
console.log("🔎 Root Element Found:", rootElement);

if (!rootElement) {
  console.error("❌ ERROR: No #root element found!");
  alert("❌ ERROR: No #root element found!");
} else {
  try {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
    console.log("✅ React has been rendered.");
    alert("✅ React has been rendered.");
  } catch (error) {
    console.error("❌ React Rendering Failed:", error);
    alert("❌ React Rendering Failed: " + error.message);
  }
}
