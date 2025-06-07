from pyrogram import filters
from pyrogram.types import Message
from Scott import app
from Scott.core.mongo import session_db

@app.on_message(filters.private & filters.command("post"))
async def handle_post(client, message: Message):
    user_id = message.from_user.id
    session = await session_db.find_one({"_id": user_id})

    if not session or not session.get("logged_in"):
        return await message.reply("❌ You are not logged in. Please login first and try again.")

    if not session.get("private_channel") or not session.get("public_channel"):
        return await message.reply("⚠️ Your channels are not fully linked. Complete registration and try again.")

    await message.reply("✅ You are logged in and channels are linked. Proceed with your post.")