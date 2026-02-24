#!/usr/bin/env python3
import time
import threading
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import db
import checkers
from config import VK_GROUP_TOKEN, CHECK_INTERVAL, STREAMERS

# ======================================================
# 📢  РАССЫЛКА
# ======================================================

def broadcast(vk, streamer_id, platform_label, title, url):
    subs = db.get_streamer_subs(streamer_id)
    if not subs:
        return
    streamer_name = next(
        (s["name"] for s in STREAMERS if s["id"] == streamer_id), streamer_id
    )
    msg = f"🔴 {streamer_name} вышел в эфир — {platform_label}!\n"
    if title:
        msg += f"📌 {title}\n"
    if url:
        msg += f"🔗 {url}"
    
    print(f"[BROADCAST] {streamer_name} / {platform_label} → {len(subs)} users")
    for uid in subs:
        try:
            vk.messages.send(
                user_id=uid, message=msg,
                random_id=int(time.time() * 1000 + uid) % 2**31
            )
            time.sleep(0.05)
        except Exception as e:
            print(f"  ✗ uid={uid}: {e}")


# ======================================================
# ⏱️  ЦИКЛ ПРОВЕРКИ
# ======================================================

PLATFORM_CHECKS = [
    ("twitch",  "🟣 Twitch",      lambda s: checkers.check_twitch(
        s["twitch"], s["twitch_id"], s["twitch_secret"]),
        lambda s: f"https://twitch.tv/{s['twitch']}"),

    ("youtube", "🔴 YouTube",     lambda s: checkers.check_youtube(
        s["youtube_channel_id"], s["youtube_api_key"]),
        lambda s: f"https://youtube.com/channel/{s['youtube_channel_id']}/live"),

    ("kick",    "🟢 KICK",        lambda s: checkers.check_kick(s["kick"]),
        lambda s: f"https://kick.com/{s['kick']}"),

    ("vkplay",  "🎮 VK Play Live", lambda s: checkers.check_vkplay(s["vkplay"]),
        lambda s: f"https://vkplay.live/{s['vkplay']}"),
]

def check_loop(vk):
    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Checking...")
        
        for s in STREAMERS:
            sid = s["id"]
            
            # API/HTML платформы
            for key, label, checker, url_fn in PLATFORM_CHECKS:
                try:
                    live, title = checker(s)
                    if live is None:
                        continue
                    was = db.get_state(sid, key)
                    if live and not was:
                        db.set_state(sid, key, True)
                        broadcast(vk, sid, label, title, url_fn(s))
                    elif not live and was:
                        db.set_state(sid, key, False)
                except Exception as e:
                    print(f"  [{sid}/{key}] {e}")
            
            # Telegram канал
            try:
                live, text = checkers.check_telegram(s.get("tg_channel", ""))
                was = db.get_state(sid, "telegram")
                if live and not was:
                    db.set_state(sid, "telegram", True)
                    broadcast(vk, sid, "📣 Telegram", text,
                              f"https://t.me/{s['tg_channel']}")
                elif not live and was:
                    db.set_state(sid, "telegram", False)
            except Exception as e:
                print(f"  [{sid}/tg] {e}")
            
            # VK группа стримера
            try:
                live, text = checkers.check_vk_group(vk, s.get("vk_group", 0))
                was = db.get_state(sid, "vk_group")
                if live and not was:
                    db.set_state(sid, "vk_group", True)
                    broadcast(vk, sid, "💙 VK",  text,
                              f"https://vk.com/club{abs(s['vk_group'])}")
                elif not live and was:
                    db.set_state(sid, "vk_group", False)
            except Exception as e:
                print(f"  [{sid}/vk] {e}")
        
        time.sleep(CHECK_INTERVAL)


# ======================================================
# ⌨️  КЛАВИАТУРЫ
# ======================================================

def kb_main(uid):
    """Главная клавиатура: зависит от того, есть ли подписки"""
    kb = VkKeyboard(one_time=False)
    kb.add_button("📋 Список стримеров", VkKeyboardColor.PRIMARY)
    kb.add_line()
    subs = db.get_user_subs(uid)
    if subs:
        kb.add_button("⭐ Мои подписки",   VkKeyboardColor.SECONDARY)
        kb.add_button("❌ Отписаться",      VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()

def kb_streamers(uid):
    """Список стримеров — кнопка на каждого"""
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
    """Клавиатура для отписки — только подписанные"""
    kb = VkKeyboard(one_time=False)
    subs = db.get_user_subs(uid)
    for i, s in enumerate(STREAMERS):
        if s["id"] in subs:
            kb.add_button(f"❌ {s['name']}", VkKeyboardColor.NEGATIVE)
            if i % 2 == 1:
                kb.add_line()
    kb.add_line()
    kb.add_button("❌ Отписаться от всех", VkKeyboardColor.NEGATIVE)
    kb.add_line()
    kb.add_button("🔙 Назад", VkKeyboardColor.PRIMARY)
    return kb.get_keyboard()


# ======================================================
# 🤖  ОСНОВНОЙ БОТ
# ======================================================

def send(vk, uid, msg, keyboard=None):
    kwargs = dict(user_id=uid, message=msg,
                  random_id=int(time.time() * 1000 + uid) % 2**31)
    if keyboard:
        kwargs["keyboard"] = keyboard
    vk.messages.send(**kwargs)

def handle(vk, uid, text):
    text = text.strip()

    # Определяем шаг (состояние)
    step = db.get_step(uid)

    # ——— СТАРТ ———
    if text.lower() in ["/start", "начать", "старт"]:
        db.upsert_user(uid, "idle")
        db.set_step(uid, "idle")
        send(vk, uid,
             "👋 Привет! Я бот уведомлений о стримах.\n\n"
             "Выбери стримеров, и я оповещу тебя, когда они выйдут в эфир.",
             kb_main(uid))
        return

    # ——— СПИСОК СТРИМЕРОВ ———
    if text == "📋 Список стримеров":
        db.set_step(uid, "selecting")
        lines = []
        subs = db.get_user_subs(uid)
        for s in STREAMERS:
            mark = "✅" if s["id"] in subs else "◾"
            platforms = ", ".join(filter(None, [
                s.get("twitch") and "Twitch",
                s.get("youtube_channel_id") and "YouTube",
                s.get("kick") and "KICK",
                s.get("vkplay") and "VK Play Live",
            ]))
            lines.append(f"{mark} {s['name']} ({platforms})")
        msg = "🎮 Доступные стримеры:\n\n" + "\n".join(lines)
        msg += "\n\n👇 Нажми на имя, чтобы подписаться/отписаться"
        send(vk, uid, msg, kb_streamers(uid))
        return

    # ——— ВЫБОР СТРИМЕРА из списка ———
    if step == "selecting":
        subs = db.get_user_subs(uid)
        # Ищем нажатую кнопку (имя может быть с ✅)
        clean = text.replace("✅ ", "").replace("◾ ", "").strip()
        matched = next((s for s in STREAMERS if s["name"] == clean), None)
        
        if matched:
            sid = matched["id"]
            if sid in subs:
                db.unsubscribe(uid, sid)
                send(vk, uid, f"❌ Ты отписан от {matched['name']}", kb_streamers(uid))
            else:
                db.subscribe(uid, sid)
                send(vk, uid, f"✅ Ты подписан на {matched['name']}!\n"
                              "Получишь уведомление, как только он выйдет в эфир.",
                     kb_streamers(uid))
            return
        
        if text == "🔙 Назад":
            db.set_step(uid, "idle")
            send(vk, uid, "Главное меню:", kb_main(uid))
            return

    # ——— МОИ ПОДПИСКИ ———
    if text == "⭐ Мои подписки":
        subs = db.get_user_subs(uid)
        if not subs:
            send(vk, uid, "У тебя нет активных подписок.", kb_main(uid))
            return
        names = [s["name"] for s in STREAMERS if s["id"] in subs]
        send(vk, uid, "⭐ Твои подписки:\n\n" + "\n".join(f"• {n}" for n in names),
             kb_main(uid))
        return

    # ——— ОТПИСАТЬСЯ ———
    if text == "❌ Отписаться":
        subs = db.get_user_subs(uid)
        if not subs:
            send(vk, uid, "У тебя нет активных подписок.", kb_main(uid))
            return
        db.set_step(uid, "unsubbing")
        send(vk, uid, "От кого хочешь отписаться?", kb_unsub(uid))
        return

    if step == "unsubbing":
        if text == "❌ Отписаться от всех":
            db.unsubscribe_all(uid)
            db.set_step(uid, "idle")
            send(vk, uid, "✅ Ты отписан от всех стримеров.", kb_main(uid))
            return
        if text == "🔙 Назад":
            db.set_step(uid, "idle")
            send(vk, uid, "Главное меню:", kb_main(uid))
            return
        clean = text.replace("❌ ", "").strip()
        matched = next((s for s in STREAMERS if s["name"] == clean), None)
        if matched:
            db.unsubscribe(uid, matched["id"])
            send(vk, uid, f"✅ Ты отписан от {matched['name']}", kb_unsub(uid))
            return

    # ——— ДЕФОЛТ ———
    db.set_step(uid, "idle")
    send(vk, uid, "Используй кнопки меню 👇", kb_main(uid))


def start_bot():
    db.init_db()
    session  = vk_api.VkApi(token=VK_GROUP_TOKEN)
    vk       = session.get_api()
    longpoll = VkLongPoll(session)

    threading.Thread(target=check_loop, args=(vk,), daemon=True).start()
    print("✅ Bot started!")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                db.upsert_user(event.user_id)
                handle(vk, event.user_id, event.text)
            except Exception as e:
                print(f"[Handler error] {e}")

if __name__ == "__main__":
    start_bot()
