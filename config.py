# =====================================================
# ⚙️ ТОКЕН БОТА (твой, не стримера!)
# =====================================================
VK_GROUP_TOKEN = "vk1.a.BnQZA2TGHd8qlwoa2cPFxvIEBwTF7b55YVqOeyuHvlnXDxMuBaX6C1KO56MyEIok9ZcIauawWztl9LrMXV32x8BVGkRFZ5ZdNq2WlAyUdVk-gx9NXIWwAktOIsYH9462KLQBhZmNjpbIbZ5sW2ziT9k4gczrjq1q4jApVCCiFExZDVlVsDObJd4czFYBU0BEwrwkVLxC7c4kmj2bl3oIcA"
VK_GROUP_ID    = 236231799

CHECK_INTERVAL = 60  # секунд между проверками

# =====================================================
# 🎮 СТРИМЕРЫ — просто вставляй ссылки!
# Не нужно: API-ключи, секреты, логины стримеров
# Если платформы нет — оставь "" (пустые кавычки)
# =====================================================
STREAMERS = [
    {
        "id":          "hardplay",                 # уникальный ключ (латиница, без пробелов)
        "name":        "HARD PLAY",                # отображаемое имя в боте
        "twitch_url":  "https://twitch.tv/hardgamechannel", # Ссылка на Twitch
        "youtube_url": "https://youtube.com/@hardplayyt", # Ссылка на YouTube
        "kick_url":    "https://kick.com/hardplayofficial", # Если KICK нет, оставляем пусто
        "vkplay_url":  "https://live.vkvideo.ru/hardplay", # Ссылка на VK Play
        "tg_url":      "https://t.me/hplegion",     # Ссылка на Telegram канал
        "vk_group_url":"https://vk.com/hp_legion",      # Ссылка на VK группу
    },
    # Чтобы добавить второго стримера, раскомментируй (убери #) строки ниже:
    # {
    #     "id":          "bulkin",
    #     "name":        "Булкин",
    #     "twitch_url":  "",
    #     "youtube_url": "https://youtube.com/@bulkin",
    #     "kick_url":    "",
    #     "vkplay_url":  "",
    #     "tg_url":      "",
    #     "vk_group_url": "https://vk.com/bulkin",
    # },
]
