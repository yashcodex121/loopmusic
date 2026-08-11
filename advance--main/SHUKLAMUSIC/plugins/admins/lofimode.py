# -----------------------------------------------
# 🔸 StrangerMusic Project
# 🔹 Developed & Maintained by: Shashank Shukla (https://github.com/itzshukla)
# 📅 Copyright © 2022 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by ItzShukla
# -----------------------------------------------
from pyrogram import filters
from pyrogram.types import Message
from SHUKLAMUSIC import app
from SHUKLAMUSIC.core.call import SHUKLA
from SHUKLAMUSIC.utils.database import (
    get_audiomode,
    is_music_playing,
    set_audiomode,
)
from SHUKLAMUSIC.utils.decorators import AdminRightsCheck
from SHUKLAMUSIC.utils.inline import close_markup
from config import BANNED_USERS

MODE_LABELS = {
    "normal": "🔊 Normal",
    "eco": "🍃 Eco",
    "lofi": "🌙 Lofi",
}
MODE_ORDER = ["normal", "eco", "lofi"]


@app.on_message(
    filters.command(["audiomode", "playmode2", "lofi", "cplaymode2"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def audio_mode_cmd(cli, message: Message, _, chat_id):
    usage = (
        "🎚 <b>Audio Mode</b>\n\n"
        "Usage: <code>/audiomode normal</code> | <code>eco</code> | <code>lofi</code>\n\n"
        "<b>Normal</b> — default playback.\n"
        "<b>Eco</b> — light echo, low resource use.\n"
        "<b>Lofi</b> — slowed down with a dreamy echo.\n\n"
        "Applies to the current song instantly and every song after, "
        "until you change it again."
    )
    if len(message.command) != 2:
        current = await get_audiomode(chat_id)
        return await message.reply_text(
            f"{usage}\n\nCurrent mode: <b>{MODE_LABELS[current]}</b>"
        )

    state = message.text.split(None, 1)[1].strip().lower()
    # Backward compatible: /lofi enable|disable still works.
    if state == "enable":
        state = "lofi"
    elif state == "disable":
        state = "normal"

    if state not in MODE_ORDER:
        return await message.reply_text(usage)

    current = await get_audiomode(chat_id)
    if current == state:
        return await message.reply_text(
            f"» Audio mode is already set to {MODE_LABELS[state]}."
        )

    await set_audiomode(chat_id, state)
    if await is_music_playing(chat_id):
        try:
            await SHUKLA.apply_audio_mode(chat_id)
        except Exception:
            pass

    await message.reply_text(
        f"🎚 Audio mode set to <b>{MODE_LABELS[state]}</b> by {message.from_user.mention}",
        reply_markup=close_markup(_),
    )
