import re
import time
import requests

# ——— Умная фильтрация текста постов ———

# Ключевые слова старта стрима
STREAM_KEYWORDS = [
    "стрим", "стримлю", "начинаем", "стартуем", "выхожу в эфир",
    "начал трансляцию", "идёт эфир", "live", "в прямом эфире",
    "трансляция началась", "смотрите сейчас", "уже в эфире",
]

# Домены стрим-платформ — если ссылка есть в посте, это анонс стрима
STREAM_DOMAINS = [
    "twitch.tv", "youtube.com/watch", "youtu.be",
    "kick.com", "vkplay.live", "vk.com/video_ext",
]

def _is_stream_post(text: str) -> bool:
    """True если текст поста содержит признаки анонса/старта стрима"""
    text_lower = text.lower()
    has_keyword = any(kw in text_lower for kw in STREAM_KEYWORDS)
    has_link    = any(domain in text_lower for domain in STREAM_DOMAINS)
    return has_keyword or has_link

def _extract_title(text: str, maxlen=120) -> str:
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:maxlen]


# ——— Twitch (Официальный Helix API) ———

_twitch_tokens = {}  # {client_id: {"val": ..., "exp": ...}}

def _twitch_auth(client_id, client_secret):
    t = _twitch_tokens.get(client_id, {"val": None, "exp": 0})
    if time.time() < t["exp"] - 30:
        return t["val"]
    r = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }, timeout=10).json()
    token = {"val": r["access_token"], "exp": time.time() + r.get("expires_in", 3600)}
    _twitch_tokens[client_id] = token
    return token["val"]

def check_twitch(login, client_id, client_secret):
    if not login:
        return None, ""
    try:
        token = _twitch_auth(client_id, client_secret)
        r = requests.get(
            f"https://api.twitch.tv/helix/streams?user_login={login}",
            headers={"Client-ID": client_id, "Authorization": f"Bearer {token}"},
            timeout=10
        ).json()
        data = r.get("data", [])
        return (True, data[0].get("title", "")) if data else (False, "")
    except Exception as e:
        print(f"[Twitch:{login}] {e}"); return None, ""


# ——— YouTube Data API v3 ———

def check_youtube(channel_id, api_key):
    if not channel_id or not api_key:
        return None, ""
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet", "channelId": channel_id,
                "eventType": "live", "type": "video", "key": api_key
            }, timeout=10
        ).json()
        items = r.get("items", [])
        return (True, items[0]["snippet"]["title"]) if items else (False, "")
    except Exception as e:
        print(f"[YouTube:{channel_id}] {e}"); return None, ""


# ——— KICK.com ———

def check_kick(username):
    if not username:
        return None, ""
    try:
        r = requests.get(
            f"https://kick.com/api/v1/channels/{username}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json",
                "Referer": f"https://kick.com/{username}"
            }, timeout=15
        ).json()
        ls = r.get("livestream")
        return (True, ls.get("session_title", "")) if ls else (False, "")
    except Exception as e:
        print(f"[KICK:{username}] {e}"); return None, ""


# ——— VK Play Live (HTML) ———

def check_vkplay(username):
    if not username:
        return None, ""
    try:
        r = requests.get(
            f"https://vkplay.live/{username}",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=15
        )
        if "StreamStatus_isOnline" in r.text:
            m = re.search(r'<title>([^<]+)</title>', r.text)
            return (True, m.group(1) if m else "")
        return (False, "")
    except Exception as e:
        print(f"[VKPlay:{username}] {e}"); return None, ""


# ——— Telegram канал (HTML t.me/s/) ———

def check_telegram(channel):
    if not channel:
        return False, ""
    try:
        r = requests.get(
            f"https://t.me/s/{channel}",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=15
        )
        # Последние 5 постов
        posts = re.findall(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            r.text, re.DOTALL
        )
        for raw in reversed(posts[-5:]):
            text = re.sub(r'<[^>]+>', '', raw)
            if _is_stream_post(text):
                return True, _extract_title(text)
    except Exception as e:
        print(f"[TG:{channel}] {e}")
    return False, ""


# ——— VK Группа стримера ———

def check_vk_group(vk_api, group_id):
    if not group_id:
        return False, ""
    try:
        posts = vk_api.wall.get(owner_id=group_id, count=10).get("items", [])
        for post in posts:
            age  = time.time() - post.get("date", 0)
            text = post.get("text", "")
            # Только свежие посты (до 15 минут) + умная фильтрация
            if age < 900 and _is_stream_post(text):
                return True, _extract_title(text)
    except Exception as e:
        print(f"[VK Group:{group_id}] {e}")
    return False, ""
