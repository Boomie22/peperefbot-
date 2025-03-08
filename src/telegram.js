export function initTelegram() {
    if (typeof window !== "undefined" && window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready(); // Ensure Telegram WebApp is initialized
        tg.expand(); // Expands WebApp to full height
        console.log("✅ Telegram WebApp initialized.");
        return tg;
    } else {
        console.warn("⚠️ Telegram WebApp not available.");
        return null;
    }
}

export const tg = initTelegram();
