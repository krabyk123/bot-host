#!/usr/bin/env python3
import time
import threading
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import db
import checkers
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
                user_id=uid,
                message=msg,
                random_id=int(time.time() * 1000 + uid) % 2**31
            )
            time.sleep(0.05)
        except Exception as e:
            print(f"  error uid={uid}: {e}")


# =====================================================
# ⏱️ ЦИКЛ ПРОВЕРКИ СТРИМОВ
# =====================================================
def check_loop(vk):
    API_CHECKS = [
        ("twitch",  "Twitch",       checkers.check_twitch,  "twitch_url"),
        ("youtube", "YouTube",      checkers.check_youtube, "youtube_url"),
        ("kick",    "KICK",         checkers.check_kick,    "kick_url"),
        ("vkplay",  "VK Play Live", checkers.check_vkplay,  "vkplay_url"),
    ]
    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Проверка стримов...")
        for s in STREAMERS:
            sid = s["id"]

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

            try:
                live, text = checkers.check_telegram(s.get("tg_url", ""))
                was = db.get_state(sid, "telegram")
                if live and not was:
                    db.set_state(sid, "telegram", True)
                    broadcast(vk, sid, "Telegram", text, s.get("tg_url", ""))
                elif not live and was:
                    db.set_state(sid, "telegram", False)
            except Exception as e:
                print(f"  [{sid}/tg] {e}")

            try:
                live, text = checkers.check_vk_group(vk, s.get("vk_group_url", ""))
                was = db.get_state(sid, "vk_group")
                if live and not was:
                    db.set_state(sid, "vk_group", True)
                    broadcast(vk, sid, "VK", text, s.get("vk_group_url", ""))
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
    kb.add_button("Список стримеров", VkKeyboardColor.PRIMARY)
    kb.add_line()
    if db.get_user_subs(uid):
        kb.add_button("Мои подписки", VkKeyboardColor.SECONDARY)
        kb.add_button("Отписаться",   VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()


def kb_streamers(uid):
    kb = VkKeyboard(one_time=False)
    subs = db.get_user_subs(uid)
    for i, s in enumerate(STREAMERS):
        mark = "[v] " if s["id"] in subs else ""
        kb.add_button(mark + s["name"], VkKeyboardColor.SECONDARY)
        if i % 2 == 1 and i < len(STREAMERS) - 1:
            kb.add_line()
    kb.add_line()
    kb.add_button("Назад", VkKeyboardColor.PRIMARY)
    return kb.get_keyboard()


def kb_unsub(uid):
    kb = VkKeyboard(one_time=False)
    subs = db.get_user_subs(uid)
    added = False
    for i, s in enumerate(STREAMERS):
        if s["id"] in subs:
            kb.add_button("Отп: " + s["name"], VkKeyboardColor.NEGATIVE)
            if i % 2 == 1:
                kb.add_line()
            added = True
    if added:
        kb.add_line()
    kb.add_button("Отписаться от всех", VkKeyboardColor.NEGATIVE)
    kb.add_line()
    kb.add_button("Назад", VkKeyboardColor.PRIMARY)
    return kb.get_keyboard()


# =====================================================
# 💬 ОТПРАВКА СООБЩЕНИЯ
# =====================================================
def send(vk, uid, msg, kb=None):
    params = dict(
        user_id=uid,
        message=msg,
        random_id=int(time.time() * 1000 + uid) % 2**31
    )
    if kb:
        params["keyboard"] = kb
    vk.messages.send(**params)


# =====================================================
# 🤖 ОБРАБОТЧИК СООБЩЕНИЙ
# =====================================================
def handle(vk, uid, text):
    text = text.strip()
    step = db.get_step(uid)

    # СТАРТ
    if text.lower() in ["/start", "начать", "старт"]:
        db.upsert_user(uid, "idle")
        send(vk, uid,
             "Привет! Я бот уведомлений о стримах.\n\n"
             "Выбери стримеров и я сообщу когда они выйдут в эфир.",
             kb_main(uid))
        return

    # СПИСОК СТРИМЕРОВ
    if text == "Список стримеров":
        db.set_step(uid, "selecting")
        subs = db.get_user_subs(uid)
        lines = []
        for s in STREAMERS:
            mark = "[v]" if s["id"] in subs else "[ ]"
            plats = [k for k, v in [
                ("Twitch",  s.get("twitch_url")),
                ("YouTube", s.get("youtube_url")),
                ("KICK",    s.get("kick_url")),
                ("VKPlay",  s.get("vkplay_url")),
            ] if v]
            lines.append(mark + " " + s["name"] + " (" + (", ".join(plats) or "нет платформ") + ")")
        send(vk, uid,
             "Доступные стримеры:\n\n" + "\n".join(lines) +
             "\n\nНажми на имя — подписаться/отписаться",
             kb_streamers(uid))
        return

    # ВЫБОР СТРИМЕРА
    if step == "selecting":
        if text == "Назад":
            db.set_step(uid, "idle")
            send(vk, uid, "Главное меню:", kb_main(uid))
            return
        clean = text.replace("[v] ", "").strip()
        matched = next((s for s in STREAMERS if s["name"] == clean), None)
        if matched:
            subs = db.get_user_subs(uid)
            if matched["id"] in subs:
                db.unsubscribe(uid, matched["id"])
                send(vk, uid, "Ты отписан от " + matched["name"], kb_streamers(uid))
            else:
                db.subscribe(uid, matched["id"])
                send(vk, uid,
                     "Подписка на " + matched["name"] + " оформлена!\n"
                     "Жду когда выйдет в эфир.",
                     kb_streamers(uid))
            return

    # МОИ ПОДПИСКИ
    if text == "Мои подписки":
        subs = db.get_user_subs(uid)
        if not subs:
            send(vk, uid, "У тебя нет активных подписок.", kb_main(uid))
            return
        names = [s["name"] for s in STREAMERS if s["id"] in subs]
        send(vk, uid,
             "Твои подписки:\n" + "\n".join("- " + n for n in names),
             kb_main(uid))
        return

    # ОТПИСАТЬСЯ
    if text == "Отписаться":
        if not db.get_user_subs(uid):
            send(vk, uid, "У тебя нет активных подписок.", kb_main(uid))
            return
        db.set_step(uid, "unsubbing")
        send(vk, uid, "От кого хочешь отписаться?", kb_unsub(uid))
        return

    if step == "unsubbing":
        if text == "Отписаться от всех":
            db.unsubscribe_all(uid)
            db.set_step(uid, "idle")
            send(vk, uid, "Ты отписан от всех стримеров.", kb_main(uid))
            return
        if text == "Назад":
            db.set_step(uid, "idle")
            send(vk, uid, "Главное меню:", kb_main(uid))
            return
        clean = text.replace("Отп: ", "").strip()
        matched = next((s for s in STREAMERS if s["name"] == clean), None)
        if matched:
            db.unsubscribe(uid, matched["id"])
            send(vk, uid, "Ты отписан от " + matched["name"], kb_unsub(uid))
            return

    # ДЕФОЛТ
    db.set_step(uid, "idle")
    send(vk, uid, "Используй кнопки меню.", kb_main(uid))


# =====================================================
# 🚀 ЗАПУСК БОТА
# =====================================================
def start_bot():
    db.init_db()
    session  = vk_api.VkApi(token=VK_GROUP_TOKEN)
    vk       = session.get_api()
    longpoll = VkBotLongPoll(session, VK_GROUP_ID)

    threading.Thread(target=check_loop, args=(vk,), daemon=True).start()
    print("Bot started!")

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg_obj = event.obj.message
            uid     = msg_obj.get("from_id")
            text    = msg_obj.get("text", "")
            # Пропускаем сообщения от самой группы (uid < 0)
            if uid and uid > 0:
                try:
                    db.upsert_user(uid)
                    handle(vk, uid, text)
                except Exception as e:
                    print(f"[Handler] {e}")


if __name__ == "__main__":
    start_bot()
