# =====================================================
# ⚙️ ТОКЕН БОТА (твой, не стримера!)
# =====================================================
VK_GROUP_TOKEN = "vk1.a.M2NzVybh-yEfXDAM5cS0Yv5TawW50Vf40_7JWXuu2kI7ekAQZ27gAM4drtLQPAhmP1jerRevby_XsaWec7X0efEZkgBv_B-XaGGeJBN-_A4_jKMcsUDrjSkHfar7HTLXOdSR7fEVa8Y8DBbeIN6vAeeqBwx8avNUD8VGutkvCP9T90C5NRj5pEVk_ZJYXB6xJpbfdz4NLKVQyFFDg40W1Q"
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
