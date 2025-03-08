import { useEffect, useState } from "react";
import { tg } from "./telegram";

function App() {
  const [caption, setCaption] = useState("🔥 Join the PepeRefBot! Earn rewards by sharing this story!");
  const [isTelegram, setIsTelegram] = useState(false);

  useEffect(() => {
    console.log("🚀 App is initializing...");
    console.log("🔍 Checking if Telegram WebApp is available:", tg);

    if (window.Telegram && window.Telegram.WebApp) {
      console.log("✅ Telegram WebApp detected!");
      setIsTelegram(true);
      window.Telegram.WebApp.ready();
    } else {
      console.warn("⚠️ Running in a regular browser, not Telegram");
    }
  }, []);

  if (!isTelegram) {
    console.error("❌ ERROR: Telegram WebApp is NOT detected!");
    return <h1 style={{ textAlign: "center", padding: "20px", color: "red" }}>⚠️ Please open this in Telegram.</h1>;
  }

  const shareStory = () => {
    console.log("📤 Attempting to share story...");
    
    const imageURL = "https://source.unsplash.com/random/800x600";
    const shareLink = `tg://story?photo=${encodeURIComponent(imageURL)}&text=${encodeURIComponent(caption)}`;

    console.log("🔗 Generated Share Link:", shareLink);

    if (!window.Telegram) {
      console.error("❌ ERROR: Telegram WebApp API is missing.");
      alert("⚠️ Telegram API is not available!");
      return;
    }

    window.location.href = shareLink;
  };

  return (
    <div style={{ textAlign: "center", padding: "20px" }}>
      <h1>📢 Share Your Story</h1>
      <img src="https://source.unsplash.com/random/800x600" alt="Referral Banner" width="100%" />
      <textarea
        value={caption}
        onChange={(e) => setCaption(e.target.value)}
        style={{ width: "90%", height: "50px", margin: "10px" }}
      />
      <button 
        onClick={shareStory} 
        style={{ padding: "10px", fontSize: "16px", cursor: "pointer", backgroundColor: "#0088cc", color: "white", border: "none", borderRadius: "5px" }}
      >
        📤 Share to Telegram Story
      </button>
    </div>
  );
}

export default App;
