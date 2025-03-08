import { useEffect, useState } from "react";
import { tg, initTelegram } from "./telegram";

function App() {
    const [caption, setCaption] = useState("🔥 Join the PepeRefBot! Use my referral link to earn rewards!");
    const [isTelegram, setIsTelegram] = useState(!!tg); // Detect if inside Telegram

    useEffect(() => {
        initTelegram();
    }, []);

    const handleShareStory = () => {
        if (!isTelegram) {
            alert("This feature only works inside Telegram Mini Apps.");
            return;
        }

        const imageURL = "https://your-render-app.onrender.com/assets/referral_banner.jpg";
        tg.shareToStory(imageURL, { text: caption });
    };

    return (
        <div className="app" style={{ textAlign: "center", padding: "20px" }}>
            <h1>📢 Share Your Story</h1>
            {isTelegram ? (
                <>
                    <img src="https://your-render-app.onrender.com/assets/referral_banner.jpg" alt="Referral Banner" width="100%" />
                    <textarea 
                        value={caption} 
                        onChange={(e) => setCaption(e.target.value)} 
                        style={{ width: "90%", height: "50px", margin: "10px" }}
                    />
                    <button onClick={handleShareStory} style={{ padding: "10px", fontSize: "16px", cursor: "pointer" }}>
                        📤 Share to Telegram Story
                    </button>
                </>
            ) : (
                <p>❌ Please open this Mini App inside Telegram.</p>
            )}
        </div>
    );
}

export default App;
