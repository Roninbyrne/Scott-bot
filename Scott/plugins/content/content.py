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
    EMAIL_BODY_FINAL,
    EMAIL_SUBJECT_DELETE_OTP,
    EMAIL_BODY_DELETE_OTP,
    EMAIL_SUBJECT_DELETE_FINAL,
    EMAIL_BODY_DELETE_FINAL,
)

otp_cache = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def generate_login_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

async def send_otp_email(receiver_email: str, otp: str, name: str):
    msg = EmailMessage()
    msg["Subject"] = EMAIL_SUBJECT_OTP
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg.add_alternative(EMAIL_BODY_OTP.format(name=name, otp=otp), subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

async def send_delete_otp_email(receiver_email: str, otp: str, name: str):
    msg = EmailMessage()
    msg["Subject"] = EMAIL_SUBJECT_DELETE_OTP
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg.add_alternative(EMAIL_BODY_DELETE_OTP.format(name=name, otp=otp), subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

async def send_final_email(receiver_email: str, login_id: str, password: str, private_id: int, public_id: int, name: str):
    private = await group_log_db.find_one({"_id": private_id})
    public = await group_log_db.find_one({"_id": public_id})
    private_name = private["title"] if private else "Unknown"
    public_name = public["title"] if public else "Unknown"
    html = EMAIL_BODY_FINAL.format(
        name=name,
        login_id=login_id,
        password=password,
        private_id=private_id,
        public_id=public_id,
        private_name=private_name,
        public_name=public_name
    )
    msg = EmailMessage()
    msg["Subject"] = EMAIL_SUBJECT_FINAL
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

async def send_delete_final_email(receiver_email: str, login_id: str, name: str):
    msg = EmailMessage()
    msg["Subject"] = EMAIL_SUBJECT_DELETE_FINAL
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg.add_alternative(EMAIL_BODY_DELETE_FINAL.format(name=name, login_id=login_id), subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

command_buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🔐 Register", callback_data="start_register"),
        InlineKeyboardButton("🔓 Login", callback_data="start_login")
    ],
    [
        InlineKeyboardButton("❌ Exit", callback_data="cancel_register")
    ]
])

logged_in_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("🗑️ Delete Data Permanently", callback_data="delete_data_permanently")],
    [InlineKeyboardButton("✅ Check Connected Channels", callback_data="check_channels")],
    [
        InlineKeyboardButton("🚪 Logout", callback_data="logout_user"),
        InlineKeyboardButton("❌ Exit", callback_data="cancel_register")
    ]
])

@app.on_callback_query(filters.regex("command_menu"))
async def help_menu(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = await session_db.find_one({"_id": user_id})
    if session and session.get("logged_in"):
        await callback_query.message.edit_text(
            "✅ You are already logged in.",
            reply_markup=logged_in_buttons
        )
    else:
        await callback_query.message.edit_text(
            "📜 <b>Use the buttons below to Register or Login:</b>",
            reply_markup=command_buttons
        )

@app.on_callback_query(filters.regex("cancel_register"))
async def cancel_register(client, callback_query: CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.answer("❌ Menu closed.", show_alert=True)

@app.on_callback_query(filters.regex("start_register"))
async def start_register(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await session_db.update_one({"_id": user_id}, {"$set": {
        "step": "name",
        "tries": 0
    }}, upsert=True)
    await callback_query.message.edit_text("📝 Please enter your full name to begin registration.")

@app.on_callback_query(filters.regex("start_login"))
async def start_login(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = await session_db.find_one({"_id": user_id})
    if session and session.get("logged_in"):
        return await callback_query.answer("⚠️ You are already logged in. Logout first.", show_alert=True)
    await session_db.update_one({"_id": user_id}, {"$set": {
        "step": "login_id"
    }}, upsert=True)
    await callback_query.message.edit_text("🔐 Please enter your Login ID.")

@app.on_callback_query(filters.regex("check_channels"))
async def check_connected_channels(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = await session_db.find_one({"_id": user_id})
    if not session or not session.get("logged_in"):
        return await callback_query.message.edit_text("❌ You're not logged in.")
    login_id = session.get("login_id")
    private_id = session.get("private_channel")
    public_id = session.get("public_channel")
    private_group = await group_log_db.find_one({"_id": private_id})
    public_group = await group_log_db.find_one({"_id": public_id})
    private_name = private_group["title"] if private_group else "Unknown"
    public_name = public_group["title"] if public_group else "Unknown"
    await callback_query.message.edit_text(
        f"🔐 <b>Login ID:</b> <code>{login_id}</code>\n"
        f"🔒 <b>Private Channel:</b> {private_name} ({private_id})\n"
        f"📢 <b>Public Channel:</b> {public_name} ({public_id})",
        reply_markup=logged_in_buttons
    )

@app.on_callback_query(filters.regex("logout_user"))
async def logout_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = await session_db.find_one({"_id": user_id})
    if not session or not session.get("logged_in"):
        return await callback_query.answer("❌ You're not logged in.", show_alert=True)
    await session_db.delete_one({"_id": user_id})
    await callback_query.message.edit_text("✅ You've been logged out.")

@app.on_callback_query(filters.regex("delete_data_permanently"))
async def delete_data_permanently(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = await session_db.find_one({"_id": user_id})
    if not session or not session.get("logged_in"):
        return await callback_query.answer("❌ You're not logged in.", show_alert=True)
    email = session.get("email")
    name = session.get("name")
    otp = generate_otp()
    otp_cache[user_id] = {"otp": otp, "count": 1, "expires": asyncio.get_event_loop().time() + 300, "type": "delete"}
    await session_db.update_one({"_id": user_id}, {"$set": {"step": "delete_otp"}})
    try:
        await send_delete_otp_email(email, otp, name)
        await callback_query.message.edit_text(f"📨 OTP sent to {email} for account deletion. Submit it here within 5 minutes.")
    except Exception:
        await callback_query.message.edit_text("❌ Failed to send email. Please try again later.")