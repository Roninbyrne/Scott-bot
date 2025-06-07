from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyrogram.filters import Filter
from Scott import app
from Scott.core.mongo import session_db, register_data_db

user_states = {}

class InPostingFlow(Filter):
    def __init__(self):
        super().__init__()

    async def __call__(self, client, message):
        user_id = message.from_user.id
        state = user_states.get(user_id)
        return state and state.get("step") in ["awaiting_description", "awaiting_photo"]

in_posting_flow = InPostingFlow()

@app.on_callback_query(filters.regex("search_user_status"))
async def search_user_status(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    session = await session_db.find_one({"_id": user_id})
    if not session or not session.get("logged_in"):
        return await callback_query.message.edit_text(
            "❌ You are not logged in. Please log in first using your Login ID."
        )

    login_id = session.get("login_id")
    if not login_id:
        return await callback_query.message.edit_text(
            "⚠️ Login ID not found in session. Please log in again."
        )

    register_data = await register_data_db.find_one({"_id": login_id})
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

    if public_channel:
        await client.send_message(
            chat_id=user_id,
            text="📝 Please send the description you'd like to post."
        )
        user_states[user_id] = {
            "step": "awaiting_description",
            "public_channel": public_channel
        }

@app.on_message(filters.private & filters.text & in_posting_flow)
async def handle_description(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state["step"] == "awaiting_description":
        state["description"] = message.text
        state["step"] = "awaiting_photo"
        await message.reply("📷 Now, please send the cover photo.")
    elif state["step"] == "awaiting_photo":
        await message.reply("❗ Please send a photo, not text.")

@app.on_message(filters.private & filters.photo & in_posting_flow)
async def handle_photo(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state["step"] == "awaiting_photo":
        await client.send_photo(
            chat_id=state["public_channel"],
            photo=message.photo.file_id,
            caption=state["description"]
        )
        await message.reply("✅ Your post has been sent to the public channel!")
        user_states.pop(user_id)