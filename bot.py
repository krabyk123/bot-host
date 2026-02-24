#!/usr/bin/env python3
import time
import threading
import vk_api
# ВАЖНО: Теперь используем BotLongPoll для токенов сообществ
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import db
import checkers
# Добавили импорт VK_GROUP_ID
from config import VK_GROUP_TOKEN, VK_GROUP_ID, CHECK_INTERVAL, STREAMERS

# =====================================================
# 📢 РАССЫЛКА
# =====================================================
def broadcast(vk, streamer_id, label, title, url):
    subs = db.get_streamer_subs(streamer_id)
    if not subs:
        return
    name = next((s["name"] for s in STREAMERS if s["id"] == streamer_id), streamer_id)
    msg = f"🔴 {name} вышел в эфир — {label}!\n"
    if title:
        msg += f"📌 {title}\n"
    if url:
        msg += f"🔗 {url}"
    print(f"[BROADCAST] {name}/{label} → {len(subs)} users")
    for uid in subs:
        try:
            vk.messages.send(
                user_id=uid, message=msg,
                random_id=int(time.time() * 1000 + uid) % 2**31
            )
            time.sleep(0.05)
        except Exception as e:
            print(f"  ✗ {uid}: {e}")

# =====================================================
# ⏱️ ЦИКЛ ПРОВЕРКИ
# =====================================================
def check_loop(vk):
    API_CHECKS = [
        ("twitch",  "🟣 Twitch",       checkers.check_twitch,  "twitch_url"),
        ("youtube", "🔴 YouTube",       checkers.check_youtube, "youtube_url"),
        ("kick",    "🟢 KICK",          checkers.check_kick,    "kick_url"),
        ("vkplay",  "🎮 VK Play Live",  checkers.check_vkplay,  "vkplay_url"),
    ]
    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Проверка стримов...")
        for s in STREAMERS:
            sid = s["id"]
            # Стриминговые платформы
            for key, label, fn, url_key in API_CHECKS:
                try:
                    live, title = fn(s.get(url_key, ""))
                    if live is None:
                        continue
                    was = db.get_state(sid, key)
                    if live and not was:
                        db.set_state(sid, key, True)
                        broadcast(vk, sid, label, title, s.get(url_key, ""))
                    elif not live and was:
                        db.set_state(sid, key, False)
                except Exception as e:
                    print(f"  [{sid}/{key}] {e}")
            # Telegram
            try:
                live, text = checkers.check_telegram(s.get("tg_url", ""))
                was = db.get_state(sid, "telegram")
                if live and not was:
                    db.set_state(sid, "telegram", True)
                    broadcast(vk, sid, "📣 Telegram", text, s.get("tg_url", ""))
                elif not live and was:
                    db.set_state(sid, "telegram", False)
            except Exception as e:
                print(f"  [{sid}/tg] {e}")
            # VK Группа стримера
            try:
                live, text = checkers.check_vk_group(vk, s.get("vk_group_url", ""))
                was = db.get_state(sid, "vk_group")
                if live and not was:
                    db.set_state(sid, "vk_group", True)
                    broadcast(vk, sid, "💙 VK", text, s.get("vk_group_url", ""))
                elif not live and was:
                    db.set_state(sid, "vk_group", False)
            except Exception as e:
                print(f"  [{sid}/vk] {e}")
        time.sleep(CHECK_INTERVAL)

# =====================================================
# ⌨️ КЛАВИАТУРЫ
# =====================================================
def kb_main(uid):
    kb = VkKeyboard(one_time=False)
    kb.add_button("📋 Список стримеров", VkKeyboardColor.PRIMARY)
    kb.add_line()
    if db.get_user_subs(uid):
        kb.add_button("⭐ Мои подписки", VkKeyboardColor.SECONDARY)
        kb.add_button("❌ Отписаться",    VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()

def kb_streamers(uid):
    kb = VkKeyboard(one_time=False)
    subs = db.get_user_subs(uid)
    for i, s in enumerate(STREAMERS):
        mark = "✅ " if s["id"] in subs else ""
        kb.add_button(f"{mark}{s['name']}", VkKeyboardColor.SECONDARY)
        if i % 2 == 1 and i < len(STREAMERS) - 1:
            kb.add_line()
    kb.add_line()
    kb.add_button("🔙 Назад", VkKeyboardColor.PRIMARY)
    return kb.get_keyboard()

def kb_unsub(uid):
    kb = VkKeyboard(one_time=False)
    subs = db.get_user_subs(uid)
    for i, s in enumerate(STREAMERS):
        if s["id"] in subs:
            kb.add_button(f"❌ {s['name']}", VkKeyboardColor.NEGATIVE)
            if i % 2 == 1:
                kb.add_line()
    kb.add_line()
    kb.add_button("❌ Все сразу", VkKeyboardColor.NEGATIVE)
    kb.add_line()
    kb.add_button("🔙 Назад", VkKeyboardColor.PRIMARY)
    return kb.get_keyboard()

# =====================================================
# 🤖 ОБРАБОТЧИК СООБЩЕНИЙ
# =====================================================
def send(vk, uid, msg, kb=None):
    vk.messages.send(
        user_id=uid, message=msg,
        random_id=int(time.time() * 1000 + uid) % 2**31,
        **({"keyboard": kb} if kb else {})
    )

def handle(vk, uid, text):
    text = text.strip()
    step = db.get_step(uid)

    if text.lower() in ["/start", "начать", "старт"]:
        db.upsert_user(uid, "idle")
        send(vk, uid,
             "👋 Привет! Я бот уведомлений о стримах.\n\n"
             "Выбери стримеров — и я сообщу, как только они выйдут в эфир 🔴",
             kb_main(uid))
        return

    if text == "📋 Список стримеров":
        db.set_step(uid, "selecting")
        subs = db.get_user_subs(uid)
        lines = []
        for s in STREAMERS:
            mark = "✅" if s["id"] in subs else "◾"
            plats = [k for k, v in [
                ("Twitch", s.get("twitch_url")), ("YouTube", s.get("youtube_url")),
                ("KICK",   s.get("kick_url")),   ("VKPlay",  s.get("vkplay_url"))
            ] if v]
            lines.append(f"{mark} {s['name']} ({', '.join(plats) or '—'})")
        send(vk, uid,
             "🎮 Доступные стримеры:\n\n" + "\n".join(lines) +
             "\n\n👇 Нажми на имя — подписка/отписка",
             kb_streamers(uid))
        return

    if step == "selecting":
        clean = text.replace("✅ ", "").replace("◾ ", "").strip()
        m = next((s for s in STREAMERS if s["name"] == clean), None)
        if m:
            subs = db.get_user_subs(uid)
            if m["id"] in subs:
                db.unsubscribe(uid, m["id"])
                send(vk, uid, f"❌ Ты отписан от {m['name']}", kb_streamers(uid))
            else:
                db.subscribe(uid, m["id"])
                send(vk, uid,
                     f"✅ Подписка на {m['name']} оформлена!\n"
                     "Жди уведомления когда выйдет в эфир 🎮",
                     kb_streamers(uid))
            return
        if text == "🔙 Назад":
            db.set_step(uid, "idle"); send(vk, uid, "Меню:", kb_main(uid)); return

    if text == "⭐ Мои подписки":
        subs = db.get_user_subs(uid)
        if not subs:
            send(vk, uid, "Нет активных подписок.", kb_main(uid)); return
        names = [s["name"] for s in STREAMERS if s["id"] in subs]
        send(vk, uid, "⭐ Твои подписки:\n" + "\n".join(f"• {n}" for n in names),
             kb_main(uid))
        return

    if text == "❌ Отписаться":
        if not db.get_user_subs(uid):
            send(vk, uid, "Нет активных подписок.", kb_main(uid)); return
        db.set_step(uid, "unsubbing")
        send(vk, uid, "От кого отписаться?", kb_unsub(uid))
        return

    if step == "unsubbing":
        if text == "❌ Все сразу":
            db.unsubscribe_all(uid); db.set_step(uid, "idle")
            send(vk, uid, "✅ Отписан от всех.", kb_main(uid)); return
        if text == "🔙 Назад":
            db.set_step(uid, "idle"); send(vk, uid, "Меню:", kb_main(uid)); return
        clean = text.replace("❌ ", "").strip()
        m = next((s for s in STREAMERS if s["name"] == clean), None)
        if m:
            db.unsubscribe(uid, m["id"])
            send(vk, uid, f"✅ Отписан от {
