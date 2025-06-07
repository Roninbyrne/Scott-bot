from pyrogram import filters
from pyrogram.types import CallbackQuery
from Scott import app
from Scott.core.mongo import session_db

@app.on_callback_query(filters.regex("search_user_status"))
async def search_user_status(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = await session_db.find_one({"_id": user_id})

    if not session:
        text = "❌ You have not logged in yet. Please log in to continue."
    elif not session.get("logged_in"):
        text = "⚠️ You are registered but not logged in. Please complete login."
    elif not session.get("linked_chat"):
        text = "🔗 You're logged in, but no chat is linked. Connect a group/private chat."
    else:
        chat_id = session["linked_chat"]
        text = f"✅ Login verified!\n🔗 Connected Chat ID: <code>{chat_id}</code>"

    await callback_query.message.edit_text(text)