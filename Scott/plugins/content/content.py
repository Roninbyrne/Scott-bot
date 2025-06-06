import asyncio
import random
import string
import smtplib
from email.message import EmailMessage

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from Scott import app

from Scott.core.mongo import session_db, register_data_db, group_log_db
from config import EMAIL_SENDER, EMAIL_PASSWORD

otp_cache = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def generate_login_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

async def send_otp_email(receiver_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Your OTP Verification Code"
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg.set_content(f"Your OTP is: {otp}\nIt will expire in 5 minutes.")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

command_buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🔐 Register", callback_data="start_register"),
        InlineKeyboardButton("🔓 Login", callback_data="start_login")
    ],
    [
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_register")
    ]
])

@app.on_callback_query(filters.regex("command_menu"))
async def help_menu(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        "📜 <b>Use the buttons below to Register or Login:</b>",
        reply_markup=command_buttons
    )

@app.on_callback_query(filters.regex("cancel_register"))
async def cancel_register(client, callback_query: CallbackQuery):
    await session_db.delete_one({"_id": callback_query.from_user.id})
    await callback_query.message.edit_text("❌ Registration/Login process cancelled.")

@app.on_callback_query(filters.regex("start_register"))
async def start_register(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await session_db.update_one({"_id": user_id}, {"$set": {
        "step": "email",
        "tries": 0
    }}, upsert=True)
    await callback_query.message.edit_text("📧 Please enter your Gmail ID to begin registration.")

@app.on_callback_query(filters.regex("start_login"))
async def start_login(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = await session_db.find_one({"_id": user_id})
    if session and session.get("login_id"):
        return await callback_query.answer("⚠️ You are already logged in. Logout first.", show_alert=True)
    await session_db.update_one({"_id": user_id}, {"$set": {
        "step": "login_id"
    }}, upsert=True)
    await callback_query.message.edit_text("🔐 Please enter your Login ID.")

@app.on_message(filters.private & filters.text & ~filters.command)
async def handle_registration_flow(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    session = await session_db.find_one({"_id": user_id})

    if not session:
        return

    step = session.get("step")

    if step == "email":
        if not text.endswith("@gmail.com"):
            return await message.reply("❌ Please enter a valid Gmail ID.")
        otp = generate_otp()
        otp_cache[user_id] = {"otp": otp, "count": 1, "expires": asyncio.get_event_loop().time() + 300}
        await session_db.update_one({"_id": user_id}, {"$set": {
            "email": text,
            "step": "otp"
        }})
        try:
            await send_otp_email(text, otp)
            await message.reply(f"📨 OTP sent to {text}. Check your Gmail inbox/spam.\n\n🕔 It will expire in 5 minutes.\n\nSend the OTP here.")
        except Exception:
            await message.reply("❌ Failed to send email. Check if the Gmail or App Password is correct.")
            await session_db.delete_one({"_id": user_id})
            otp_cache.pop(user_id, None)

    elif step == "otp":
        cached = otp_cache.get(user_id)
        if not cached or asyncio.get_event_loop().time() > cached["expires"]:
            await session_db.delete_one({"_id": user_id})
            otp_cache.pop(user_id, None)
            return await message.reply("❌ OTP expired. Please restart the registration.")
        if cached["otp"] != text:
            cached["count"] += 1
            if cached["count"] > 2:
                await session_db.delete_one({"_id": user_id})
                otp_cache.pop(user_id, None)
                return await message.reply("❌ Too many wrong attempts. Registration cancelled.")
            return await message.reply("❌ Incorrect OTP. Try again.")
        login_id = generate_login_id()
        await session_db.update_one({"_id": user_id}, {"$set": {
            "step": "ask_channels",
            "login_id": login_id
        }})
        otp_cache.pop(user_id, None)
        return await message.reply("✅ OTP verified.\n\nSend the **Private Channel ID** (bot must be added).")

    elif step == "ask_channels" and "private_channel" not in session:
        try:
            private_channel = int(text)
        except ValueError:
            return await message.reply("❌ Invalid private channel ID.")
        exists = await group_log_db.find_one({"_id": private_channel})
        if not exists:
            return await message.reply("❌ Bot not found in this private channel.")
        await session_db.update_one({"_id": user_id}, {"$set": {
            "private_channel": private_channel,
            "step": "ask_public_channel"
        }})
        return await message.reply("✅ Private channel verified.\nNow send **Public Channel ID**.")

    elif step == "ask_public_channel" and "public_channel" not in session:
        try:
            public_channel = int(text)
        except ValueError:
            return await message.reply("❌ Invalid public channel ID.")
        exists = await group_log_db.find_one({"_id": public_channel})
        if not exists:
            return await message.reply("❌ Bot not found in this public channel.")
        await session_db.update_one({"_id": user_id}, {"$set": {
            "public_channel": public_channel,
            "step": "ask_password"
        }})
        return await message.reply("✅ Public channel verified.\nNow send a **8-digit password** to complete registration.")

    elif step == "ask_password":
        if len(text) < 8:
            return await message.reply("❌ Password must be at least 8 characters.")
        login_id = session["login_id"]
        await register_data_db.insert_one({
            "_id": login_id,
            "user_id": user_id,
            "email": session["email"],
            "private_channel": session["private_channel"],
            "public_channel": session["public_channel"],
            "password": text
        })
        await session_db.delete_one({"_id": user_id})
        await message.reply(
            f"✅ Registration Completed!\n\n<b>Login ID:</b> <code>{login_id}</code>\n<b>Password:</b> <code>{text}</code>"
        )

    elif step == "login_id":
        data = await register_data_db.find_one({"_id": text})
        if not data:
            return await message.reply("❌ Login ID not found.")
        existing = await session_db.find_one({"login_id": text})
        if existing and existing["_id"] != user_id:
            return await message.reply("⚠️ This Login ID is already used in another session. Ask them to logout.")
        already = await session_db.find_one({"_id": user_id})
        if already and already.get("login_id"):
            return await message.reply("⚠️ You are already logged in. Use /logout to switch accounts.")
        await session_db.update_one({"_id": user_id}, {"$set": {
            "step": "login_pass",
            "login_id": text
        }})
        return await message.reply("🔑 Now enter your password:")

    elif step == "login_pass":
        login_id = session["login_id"]
        data = await register_data_db.find_one({"_id": login_id})
        if not data or data["password"] != text:
            return await message.reply("❌ Incorrect password.")
        await session_db.update_one({"_id": user_id}, {"$set": {
            "email": data["email"],
            "logged_in": True,
            "step": None
        }})
        return await message.reply(f"✅ Logged in as <code>{login_id}</code>.\nUse /logout to logout.")

@app.on_message(filters.command("logout") & filters.private)
async def logout_user(client, message: Message):
    user_id = message.from_user.id
    session = await session_db.find_one({"_id": user_id})
    if not session or not session.get("logged_in"):
        return await message.reply("❌ You're not logged in.")
    await session_db.delete_one({"_id": user_id})
    await message.reply("✅ You've been logged out.")