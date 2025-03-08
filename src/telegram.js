export const tg = typeof window !== "undefined" && window.Telegram ? window.Telegram.WebApp : null;

export function initTelegram() {
    if (tg) {
        tg.ready(); // Ensures Telegram WebApp is initialized
        tg.expand(); // Expands WebApp to full height
        tg.MainButton.text = "Share Story";
        tg.MainButton.show();
    } else {
        console.warn("Telegram WebApp not available. Are you running this inside Telegram?");
    }
}
