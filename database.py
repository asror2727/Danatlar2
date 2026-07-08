"""
Barcha SQLite bilan ishlash shu yerda.
Jadvallar: users, channels, posts, payments
"""
from __future__ import annotations

import time
import aiosqlite

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_tg_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    title TEXT,
    username TEXT,
    is_verified INTEGER DEFAULT 0,
    show_payments_to_subs INTEGER DEFAULT 1,
    created_at INTEGER,
    UNIQUE(owner_tg_id, chat_id)
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    owner_tg_id INTEGER NOT NULL,
    content_type TEXT,          -- text | photo | video | document
    file_id TEXT,
    text TEXT,
    title TEXT,                 -- post nomi (masalan "Nonga")
    payment_scope TEXT,         -- post | general | hidden
    show_to_subscribers INTEGER DEFAULT 1,
    channel_message_id INTEGER,
    created_at INTEGER,
    FOREIGN KEY(channel_id) REFERENCES channels(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,            -- NULL bo'lishi mumkin (umumiy/general donat bo'lsa)
    channel_id INTEGER NOT NULL,
    donor_tg_id INTEGER,
    donor_name TEXT,
    comment TEXT,
    amount INTEGER NOT NULL,
    provider TEXT,               -- click | payme
    provider_transaction_id TEXT,
    status TEXT DEFAULT 'pending',  -- pending | paid | cancelled
    created_at INTEGER,
    paid_at INTEGER
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def upsert_user(tg_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (tg_id, username, full_name, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(tg_id) DO UPDATE SET username=excluded.username,
                                                 full_name=excluded.full_name""",
            (tg_id, username, full_name, int(time.time())),
        )
        await db.commit()


async def add_channel(owner_tg_id: int, chat_id: int, title: str, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO channels (owner_tg_id, chat_id, title, username, is_verified, created_at)
               VALUES (?, ?, ?, ?, 1, ?)
               ON CONFLICT(owner_tg_id, chat_id) DO UPDATE SET
                    title=excluded.title, username=excluded.username, is_verified=1""",
            (owner_tg_id, chat_id, title, username, int(time.time())),
        )
        await db.commit()


async def get_channel_by_owner(owner_tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM channels WHERE owner_tg_id = ? ORDER BY id DESC LIMIT 1",
            (owner_tg_id,),
        )
        return await cur.fetchone()


async def get_channel_by_id(channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
        return await cur.fetchone()


async def set_channel_visibility(channel_id: int, show: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE channels SET show_payments_to_subs = ? WHERE id = ?",
            (1 if show else 0, channel_id),
        )
        await db.commit()


async def create_post(
    channel_id: int,
    owner_tg_id: int,
    content_type: str,
    file_id: str,
    text: str,
    title: str,
    payment_scope: str,
    show_to_subscribers: bool,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO posts (channel_id, owner_tg_id, content_type, file_id, text,
                                   title, payment_scope, show_to_subscribers, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                channel_id, owner_tg_id, content_type, file_id, text,
                title, payment_scope, 1 if show_to_subscribers else 0, int(time.time()),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def set_post_channel_message_id(post_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE posts SET channel_message_id = ? WHERE id = ?", (message_id, post_id)
        )
        await db.commit()


async def get_post(post_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        return await cur.fetchone()


async def create_payment(
    channel_id: int,
    post_id: int | None,
    donor_tg_id: int,
    donor_name: str,
    comment: str,
    amount: int,
    provider: str,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO payments (post_id, channel_id, donor_tg_id, donor_name, comment,
                                      amount, provider, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (post_id, channel_id, donor_tg_id, donor_name, comment, amount, provider, int(time.time())),
        )
        await db.commit()
        return cur.lastrowid


async def get_payment(payment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        return await cur.fetchone()


async def mark_payment_paid(payment_id: int, provider_transaction_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE payments SET status='paid', provider_transaction_id=?, paid_at=?
               WHERE id = ?""",
            (provider_transaction_id, int(time.time()), payment_id),
        )
        await db.commit()


async def mark_payment_cancelled(payment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE payments SET status='cancelled' WHERE id = ?", (payment_id,))
        await db.commit()


async def get_channel_total(channel_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM payments WHERE channel_id=? AND status='paid'",
            (channel_id,),
        )
        row = await cur.fetchone()
        return row[0] if row else 0


async def get_post_comments(post_id: int, limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT donor_name, comment, amount, paid_at FROM payments
               WHERE post_id=? AND status='paid' AND comment IS NOT NULL AND comment != ''
               ORDER BY paid_at DESC LIMIT ?""",
            (post_id, limit),
        )
        return await cur.fetchall()
