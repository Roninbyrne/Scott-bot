from pyrogram import filters
from pyrogram.types import Message
from Scott import app

@app.on_message(filters.private & filters.command(["post"], prefixes=["/"]))
async def handle_post(client, message: Message):
    print("Post command received")
    await message.reply("hello I'm ready to post")