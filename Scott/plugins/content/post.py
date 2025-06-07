from pyrogram import filters
from pyrogram.types import Message
from Scott import app
from Scott.core.mongo import register_data_db

@app.on_message(filters.private & filters.command("post"))
async def handle_post(client, message: Message):
    user_id = message.from_user.id
    user_data = await register_data_db.find_one({"_id": user_id})

    if not user_data:
        return await message.reply("❌ You are not logged in. Please login first and try again.")

    if not user_data.get("private_channel") or not user_data.get("public_channel"):
        return await message.reply("⚠️ Your channels are not fully linked. Complete registration and try again.")

    await message.reply("✅ You are logged in and channels are linked. Proceed with your post.")