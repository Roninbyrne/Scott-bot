from pyrogram import filters
from pyrogram.types import CallbackQuery
from Scott import app
from Scott.core.mongo import session_db, register_db

@app.on_callback_query(filters.regex("search_user_status"))
async def search_user_status(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    session = await session_db.find_one({"_id": user_id})
    if not session or not session.get("logged_in"):
        return await callback_query.message.edit_text(
            "❌ You are not logged in. Please log in first using your Login ID."
        )

    register_data = await register_db.find_one({"_id": user_id})
    if not register_data:
        return await callback_query.message.edit_text(
            "⚠️ Registration data not found. Please complete your setup."
        )

    private_channel = register_data.get("private_channel")
    public_channel = register_data.get("public_channel")

    if not private_channel and not public_channel:
        text = "🔗 You're logged in, but no channels are linked. Please link a group or channel."
    else:
        text = "✅ Login verified!"
        if private_channel:
            text += f"\n🔒 Private Channel ID: <code>{private_channel}</code>"
        if public_channel:
            text += f"\n🌐 Public Channel ID: <code>{public_channel}</code>"

    await callback_query.message.edit_text(text)