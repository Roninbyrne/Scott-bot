import asyncio
import random
import string
import smtplib
from email.message import EmailMessage

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from Scott import app

from Scott.core.mongo import session_db, register_data_db, group_log_db
from config import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_SUBJECT_OTP,
    EMAIL_SUBJECT_FINAL,
    EMAIL_BODY_OTP,
    EMAIL_BODY_FINAL
)

otp_cache = {}

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def generate_login_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def send_otp_email(to_email, otp_code):
    msg = EmailMessage()
    msg["Subject"] = EMAIL_SUBJECT_OTP
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg.set_content("HTML not supported", subtype='plain')
    msg.add_alternative(EMAIL_BODY_OTP.format(otp=otp_code), subtype='html')
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

async def send_final_email(receiver_email, login_id, password, private_id, public_id):
    msg = EmailMessage()
    msg["Subject"] = EMAIL_SUBJECT_FINAL
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    user = await register_data_db.find_one({"_id": login_id})
    name = user.get("name", "")
    msg.set_content("HTML not supported", subtype='plain')
    msg.add_alternative(EMAIL_BODY_FINAL.format(
        name=name,
        login_id=login_id,
        password=password,
        private_channel_id=private_id,
        public_channel_id=public_id
    ), subtype='html')
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

async def send_delete_final_email(receiver_email, login_id):
    msg = EmailMessage()
    msg["Subject"] = "Your Account Has Been Deleted"
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg.set_content(f"Your data associated with Login ID {login_id} has been successfully deleted.")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

@app.on_callback_query(filters.regex("start_register"))
async def start_register(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await session_db.update_one({"_id": user_id}, {"$set": {"step": "full_name", "tries": 0}}, upsert=True)
    await callback_query.message.edit_text("📝 Please enter your full name to begin registration.")

@app.on_message(filters.private & filters.text & ~filters.command([""]))
async def handle_registration_flow(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    session = await session_db.find_one({"_id": user_id})
    if not session:
        return
    step = session.get("step")

    if step == "full_name":
        if len(text) < 3:
            return await message.reply("❌ Name must be at least 3 characters.")
        await session_db.update_one({"_id": user_id}, {"$set": {"name": text, "step": "email"}})
        return await message.reply("📧 Now enter your Gmail ID to proceed.")

    elif step == "email":
        if not text.endswith("@gmail.com"):
            return await message.reply("❌ Please enter a valid Gmail ID.")
        otp = generate_otp()
        otp_cache[user_id] = {"otp": otp, "count": 1, "expires": asyncio.get_event_loop().time() + 300, "type": "register"}
        await session_db.update_one({"_id": user_id}, {"$set": {"email": text, "step": "otp"}})
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
        await session_db.update_one({"_id": user_id}, {"$set": {"step": "ask_channels", "login_id": login_id}})
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
        await session_db.update_one({"_id": user_id}, {"$set": {"private_channel": private_channel, "step": "ask_public_channel"}})
        return await message.reply("✅ Private channel verified.\nNow send **Public Channel ID**.")

    elif step == "ask_public_channel" and "public_channel" not in session:
        try:
            public_channel = int(text)
        except ValueError:
            return await message.reply("❌ Invalid public channel ID.")
        exists = await group_log_db.find_one({"_id": public_channel})
        if not exists:
            return await message.reply("❌ Bot not found in this public channel.")
        await session_db.update_one({"_id": user_id}, {"$set": {"public_channel": public_channel, "step": "ask_password"}})
        return await message.reply("✅ Public channel verified.\nNow send a **8-digit password** to complete registration.")

    elif step == "ask_password":
        if len(text) < 8:
            return await message.reply("❌ Password must be at least 8 characters.")
        login_id = session["login_id"]
        await register_data_db.insert_one({
            "_id": login_id,
            "user_id": user_id,
            "name": session.get("name", ""),
            "email": session["email"],
            "private_channel": session["private_channel"],
            "public_channel": session["public_channel"],
            "password": text
        })
        await send_final_email(
            receiver_email=session["email"],
            login_id=login_id,
            password=text,
            private_id=session["private_channel"],
            public_id=session["public_channel"]
        )
        await session_db.delete_one({"_id": user_id})
        await message.reply(
            f"✅ Registration Completed!\n\n<b>Name:</b> {session.get('name', 'Unknown')}\n<b>Login ID:</b> <code>{login_id}</code>\n<b>Password:</b> <code>{text}</code>"
        )

    elif step == "login_id":
        data = await register_data_db.find_one({"_id": text})
        if not data:
            return await message.reply("❌ Login ID not found.")
        already = await session_db.find_one({"_id": user_id})
        if already and already.get("logged_in"):
            return await message.reply("⚠️ You are already logged in. Use the button to logout.")
        await session_db.update_one({"_id": user_id}, {"$set": {"step": "login_pass", "temp_login_id": text}})
        return await message.reply("🔑 Now enter your password:")

    elif step == "login_pass":
        login_id = session.get("temp_login_id")
        data = await register_data_db.find_one({"_id": login_id})
        if not data or data["password"] != text:
            return await message.reply("❌ Incorrect password.")
        existing = await session_db.find_one({
            "login_id": login_id,
            "logged_in": True,
            "_id": {"$ne": user_id}
        })
        if existing:
            return await message.reply("⚠️ This Login ID is already used in another session. Ask them to logout.")
        await session_db.update_one({"_id": user_id}, {
            "$set": {
                "name": data.get("name", ""),
                "email": data["email"],
                "logged_in": True,
                "step": None,
                "login_id": login_id,
                "private_channel": data["private_channel"],
                "public_channel": data["public_channel"]
            },
            "$unset": {"temp_login_id": ""}
        })
        return await message.reply(f"✅ Logged in as <b>{data.get('name', 'User')}</b> (<code>{login_id}</code>).\nUse the command menu to check status or logout.")

    elif step == "delete_otp":
        cached = otp_cache.get(user_id)
        if not cached or asyncio.get_event_loop().time() > cached["expires"] or cached.get("type") != "delete":
            await session_db.update_one({"_id": user_id}, {"$set": {"step": None}})
            otp_cache.pop(user_id, None)
            return await message.reply("❌ OTP expired or invalid. Try again from menu.")
        if cached["otp"] != text:
            cached["count"] += 1
            if cached["count"] > 2:
                await session_db.update_one({"_id": user_id}, {"$set": {"step": None}})
                otp_cache.pop(user_id, None)
                return await message.reply("❌ Too many wrong attempts. Try again from menu.")
            return await message.reply("❌ Incorrect OTP. Try again.")
        login_id = session.get("login_id")
        email = session.get("email")
        await send_delete_final_email(email, login_id)
        await session_db.delete_one({"_id": user_id})
        await register_data_db.delete_one({"_id": login_id})
        otp_cache.pop(user_id, None)
        return await message.reply("✅ Your data has been permanently deleted. Goodbye!")