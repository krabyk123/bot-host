# ======================================================
# ⚙️ НАСТРОЙКИ БОТА
# ======================================================

VK_GROUP_TOKEN = "vk1.a.BnQZA2TGHd8qlwoa2cPFxvIEBwTF7b5SYVqOeyuHv1nXDxMuBaX6C1KO56MyEioK9ZcIauawWztl9LrMXV32x8BVGkRFZ5ZdNq2W1AyUdVk-gx9NXIWwAktOIsYH9462KLQBhZmNjpbIbZ5sW2ziT9k4gczrjq1q4jApVCCiFExZDV1VsDObJd4czFYBU0BEwrwkVLxC7c4kmj2bl3OIcA"
VK_GROUP_ID    = 236231799  # числовой ID твоей группы-бота

CHECK_INTERVAL = 60  # секунд между проверками

# ======================================================
# 🎮 СПИСОК СТРИМЕРОВ
# Добавляй сколько угодно. Если платформы нет — оставь ""
# ======================================================

STREAMERS = [
    {
        "id":           "streamer1",          # уникальный ключ (латиница, без пробелов)
        "name":         "HARD PLAY",       # отображаемое имя
        "twitch":       "streamer1_twitch",   # логин на Twitch (или "")
        "twitch_id":    "YOUR_CLIENT_ID",     # Twitch Client ID
        "twitch_secret":"YOUR_CLIENT_SECRET", # Twitch Client Secret
        "youtube_channel_id": "UCxxxxxxx",   # ID YouTube канала (или "")
        "youtube_api_key":    "YOUR_YT_KEY",  # YouTube API Key
        "kick":         "streamer1_kick",     # логин на KICK (или "")
        "vkplay":       "streamer1",          # логин на VK Play Live (или "")
        "tg_channel":   "streamer1_tg",       # имя TG канала без @ (или "")
        "vk_group":     -12345678,            # ID группы ВК (отрицательное, или 0)
    },
    {
        "id":           "streamer2",
        "name":         "Стример Два",
        "twitch":       "streamer2_twitch",
        "twitch_id":    "YOUR_CLIENT_ID_2",
        "twitch_secret":"YOUR_CLIENT_SECRET_2",
        "youtube_channel_id": "",
        "youtube_api_key":    "",
        "kick":         "",
        "vkplay":       "streamer2",
        "tg_channel":   "streamer2_tg",
        "vk_group":     -87654321,
    },
]
