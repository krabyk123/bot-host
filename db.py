import sqlite3
import json

DB = "bot.db"

def init_db():
    with sqlite3.connect(DB) as c:
        # Подписчики бота
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                step       TEXT DEFAULT 'idle'
            )
        """)
        # Подписки юзера на стримеров
        c.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id     INTEGER,
                streamer_id TEXT,
                PRIMARY KEY (user_id, streamer_id)
            )
        """)
        # Текущий статус стримов
        c.execute("""
            CREATE TABLE IF NOT EXISTS stream_state (
                streamer_id TEXT,
                platform    TEXT,
                is_live     INTEGER DEFAULT 0,
                PRIMARY KEY (streamer_id, platform)
            )
        """)


# ——— Users ———

def upsert_user(uid, step="idle"):
    with sqlite3.connect(DB) as c:
        c.execute("INSERT OR IGNORE INTO users VALUES (?, 'idle')", (uid,))
        if step != "idle":
            c.execute("UPDATE users SET step=? WHERE user_id=?", (step, uid))

def set_step(uid, step):
    with sqlite3.connect(DB) as c:
        c.execute("UPDATE users SET step=? WHERE user_id=?", (step, uid))

def get_step(uid):
    with sqlite3.connect(DB) as c:
        r = c.execute("SELECT step FROM users WHERE user_id=?", (uid,)).fetchone()
        return r[0] if r else None


# ——— Subscriptions ———

def subscribe(uid, streamer_id):
    with sqlite3.connect(DB) as c:
        c.execute("INSERT OR IGNORE INTO subscriptions VALUES (?,?)", (uid, streamer_id))

def unsubscribe(uid, streamer_id):
    with sqlite3.connect(DB) as c:
        c.execute("DELETE FROM subscriptions WHERE user_id=? AND streamer_id=?", (uid, streamer_id))

def unsubscribe_all(uid):
    with sqlite3.connect(DB) as c:
        c.execute("DELETE FROM subscriptions WHERE user_id=?", (uid,))

def get_user_subs(uid):
    with sqlite3.connect(DB) as c:
        return [r[0] for r in c.execute(
            "SELECT streamer_id FROM subscriptions WHERE user_id=?", (uid,)
        )]

def get_streamer_subs(streamer_id):
    """Все юзеры, подписанные на данного стримера"""
    with sqlite3.connect(DB) as c:
        return [r[0] for r in c.execute(
            "SELECT user_id FROM subscriptions WHERE streamer_id=?", (streamer_id,)
        )]


# ——— Stream state ———

def get_state(streamer_id, platform):
    with sqlite3.connect(DB) as c:
        r = c.execute(
            "SELECT is_live FROM stream_state WHERE streamer_id=? AND platform=?",
            (streamer_id, platform)
        ).fetchone()
        return bool(r[0]) if r else False

def set_state(streamer_id, platform, live):
    with sqlite3.connect(DB) as c:
        c.execute(
            "INSERT OR REPLACE INTO stream_state VALUES (?,?,?)",
            (streamer_id, platform, int(live))
        )
