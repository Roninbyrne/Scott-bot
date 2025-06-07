from pyrogram import filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.filters import Filter
from Scott import app
from Scott.core.mongo import session_db, register_data_db, user_states_collection, video_channels_collection
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_states = {}

class InPostingFlow(Filter):
    def __init__(self):
        super().__init__()

    async def __call__(self, client, message):
        user_id = message.from_user.id
        state = user_states.get(user_id)
        return state and state.get("step") in [
            "awaiting_description",
            "awaiting_photo",
            "get_video_link",
            "get_description",
            "get_cover_photo"
        ]

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
        user_states[user_id] = {
            "step": "get_video_link",
            "public_channel": public_channel,
            "private_channel": private_channel
        }
        await client.send_message(
            chat_id=user_id,
            text="📝 Please send the video message link to upload."
        )

@app.on_message(filters.private & filters.text & in_posting_flow)
async def handle_text_messages(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if not state:
        return

    step = state.get("step")

    if step == "get_video_link":
        video_link = message.text.strip()
        state["video_link"] = video_link
        state["step"] = "get_description"
        await message.reply("Great! Now please provide a description for the video.")

    elif step == "get_description":
        description = message.text.strip()
        state["description"] = description
        state["step"] = "get_cover_photo"
        await message.reply("Please send the cover photo.")

    elif step == "awaiting_description":
        state["description"] = message.text
        state["step"] = "awaiting_photo"
        await message.reply("📷 Now, please send the cover photo.")

    elif step == "awaiting_photo":
        await message.reply("❗ Please send a photo, not text.")

@app.on_message(filters.private & filters.photo & in_posting_flow)
async def handle_photo_messages(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if not state:
        return

    step = state.get("step")

    if step == "get_cover_photo":
        cover_photo = message.photo.file_id
        video_link = state.get("video_link")
        description = state.get("description")
        public_channel = state.get("public_channel")
        private_channel = state.get("private_channel")

        video_id = video_link.split("/")[-1]

        await post_video_to_channel(public_channel, video_id, description, cover_photo)

        await video_channels_collection.update_one(
            {"video_id": video_id},
            {"$set": {
                "public_channel": public_channel,
                "private_channel": private_channel
            }},
            upsert=True
        )

        await message.reply("✅ Video details uploaded to the public channel!")
        user_states.pop(user_id, None)

    elif step == "awaiting_photo":
        description = state.get("description")
        public_channel = state.get("public_channel")

        await client.send_photo(
            chat_id=public_channel,
            photo=message.photo.file_id,
            caption=description
        )
        await message.reply("✅ Your post has been sent to the public channel!")
        user_states.pop(user_id, None)

async def post_video_to_channel(public_channel, video_id, description, cover_photo):
    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✯ ᴅᴏᴡɴʟᴏᴀᴅ ✯", callback_data=video_id)]]
    )
    caption_text = (
        f"{description}\n\n"
        f"❱ ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ"
        f"<a href='https://t.me/phoenixXsupport'> [ ᴄʟɪᴄᴋ ʜᴇʀᴇ ]</a>"
    )
    await app.send_photo(
        chat_id=public_channel,
        photo=cover_photo,
        caption=caption_text,
        reply_markup=button,
        parse_mode="html"
    )

@app.on_callback_query()
async def handle_button_click(client, callback_query: CallbackQuery):
    video_id = callback_query.data
    user_id = callback_query.from_user.id

    video_info = await video_channels_collection.find_one({"video_id": video_id})
    if not video_info:
        await callback_query.answer("Video not found. Please try uploading again.", show_alert=True)
        return

    private_channel = video_info["private_channel"]
    try:
        message = await client.get_messages(private_channel, int(video_id))
        if message:
            if message.video:
                file_id = message.video.file_id
                sent_message = await client.send_video(user_id, file_id)
            elif message.document:
                file_id = message.document.file_id
                sent_message = await client.send_document(user_id, file_id)
            else:
                await callback_query.answer("Content is not a video or document.", show_alert=True)
                return

            await callback_query.answer("Fetching your request... Please check your DM.", show_alert=True)
            await client.send_message(
                user_id,
                "Please forward this to your saved messages and download from there. The content will be deleted after 5 minutes."
            )
            await asyncio.sleep(300)
            await client.delete_messages(user_id, sent_message.id)
        else:
            await callback_query.answer("Content not found or it's not a video/file.", show_alert=True)
    except Exception as e:
        await callback_query.answer("Failed to retrieve content.", show_alert=True)
        logger.error(f"Error fetching content: {e}")