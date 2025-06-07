from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from Scott import app
from Scott.core.mongo import global_userinfo_db
from config import SUPPORT_CHAT, SUPPORT_CHANNEL, START_VIDEO
from Scott.plugins.base.logging_toggle import is_logging_enabled
from config import LOGGER_ID

@app.on_message(filters.command("start") & filters.private)
async def start_pm(client, message: Message):
    user = message.from_user
    args = message.text.split(maxsplit=1)
    userinfo = {
        "_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "is_bot": user.is_bot
    }
    await global_userinfo_db.update_one({"_id": user.id}, {"$set": userinfo}, upsert=True)

    if await is_logging_enabled():
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "N/A"
        log_text = (
            f"📩 <b>User Started the Bot</b>\n\n"
            f"👤 <b>Name:</b> {full_name}\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"🔗 <b>Username:</b> {username}"
        )
        await client.send_message(LOGGER_ID, log_text)

    if len(args) > 1 and args[1].startswith("vid_"):
        video_id = args[1][4:]
        video_info = await client.db.video_channels_collection.find_one({"video_id": video_id})
        if video_info:
            private_channel = video_info.get("private_channel")
            try:
                msg = await client.get_messages(private_channel, int(video_id))
                if msg and (msg.video or msg.document):
                    file_id = msg.video.file_id if msg.video else msg.document.file_id
                    await client.send_message(
                        user.id,
                        "Fetching your requested video... Please wait."
                    )
                    await client.send_video(user.id, file_id) if msg.video else await client.send_document(user.id, file_id)
                    await client.send_message(
                        user.id,
                        "Please save this message. The content will be deleted after 5 minutes."
                    )
                    await asyncio.sleep(300)
                    await client.delete_messages(user.id, msg.message_id)
                else:
                    await client.send_message(user.id, "Sorry, this video is not available.")
            except Exception:
                await client.send_message(user.id, "Failed to retrieve the video. Please try again later.")
        else:
            await client.send_message(user.id, "Video not found or expired.")
        return

    text = (
        f"<b>нєу {user.first_name}.\n"
        f"๏ ɪᴍ 𝗪ᴇʀᴇᴡᴏʟꜰ 花 子 — ᴀ ᴍᴜʟᴛɪ-ᴘʟᴀʏᴇʀ ɢᴀᴍᴇ ʙᴏᴛ.\n"
        f"๏ ᴛᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ.</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me To Group ➕", url=f"https://t.me/{app.me.username}?startgroup=true")],
        [
            InlineKeyboardButton("Support Chat", url=SUPPORT_CHAT),
            InlineKeyboardButton("Support Channel", url=SUPPORT_CHANNEL)
        ],
        [
            InlineKeyboardButton("📚 Help", callback_data="help_menu"),
            InlineKeyboardButton("🧾 Commands", callback_data="command_menu")
        ],
        [InlineKeyboardButton("🔍 Search", callback_data="search_user_status")]
    ])

    await message.reply(
        f"{text}\n\n<a href='{START_VIDEO}'>๏ ʟᴇᴛ'ꜱ ʙᴇɢɪɴ ᴛʜᴇ ʜᴜɴᴛ! 🐺</a>",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("help_menu"))
async def help_menu(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣", callback_data="help_1"), InlineKeyboardButton("2️⃣", callback_data="help_2")],
        [InlineKeyboardButton("3️⃣", callback_data="help_3"), InlineKeyboardButton("4️⃣", callback_data="help_4")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])
    await callback_query.message.edit_text(
        f"<a href='{config.HELP_MENU_VIDEO}'>๏ Watch the Help Menu Video 🐺</a>\n\n📖 Choose a help topic below:",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"help_[1-4]"))
async def show_help_section(client, callback_query: CallbackQuery):
    section = callback_query.data[-1]

    help_texts = {
        "1": "📘 <b>Help Topic 1</b>\n\nYou can add full description here.",
        "2": "📙 <b>Help Topic 2</b>\n\nThis could be about how to join and start a game.",
        "3": "📗 <b>Help Topic 3</b>\n\nExplain game roles or admin commands here.",
        "4": "📕 <b>Help Topic 4</b>\n\nAdd advanced gameplay or dev info here."
    }

    help_videos = {
        "1": config.HELP_VIDEO_1,
        "2": config.HELP_VIDEO_2,
        "3": config.HELP_VIDEO_3,
        "4": config.HELP_VIDEO_4
    }

    await callback_query.message.edit_text(
        f"<a href='{help_videos[section]}'>๏ Watch Help Video 🎬</a>\n\n{help_texts[section]}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="help_menu")]
        ])
    )

@app.on_callback_query(filters.regex("close"))
async def close_menu(client, callback_query: CallbackQuery):
    await callback_query.message.delete()