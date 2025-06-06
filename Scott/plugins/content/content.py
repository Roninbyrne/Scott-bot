
import random
import string
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

COMMANDS_TEXT = "Would you like to register or login?"

REGISTER_EMAIL_TEXT = (
    "📧 Please enter your Gmail ID to begin registration.\n"
    "You will receive an OTP valid for 5 minutes (limit: 2 attempts)."
)

LOGIN_ID_TEXT = (
    "🔐 Please enter your 8-digit login ID to begin login."
)

LOGIN_ALREADY_TEXT = (
    "⚠️ You are already logged in. Please logout before trying another account."
)

command_buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🔐 Register", callback_data="start_register"),
        InlineKeyboardButton("🔓 Login", callback_data="start_login")
    ],
    [
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_register")
    ]
])

otp_cache = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def generate_login_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
