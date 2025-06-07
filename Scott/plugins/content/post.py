from pyrogram import filters
from pyrogram.types import Message
from Scott import app

@app.on_message(filters.private & filters.command("post"))
async def handle_post(client, message: Message):
    await message.reply("hello I'm ready to post")