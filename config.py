import re
from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

# Load environment variables from .env file
load_dotenv()

# Telegram API credentials (from https://my.telegram.org)
API_ID = 20948356
API_HASH = "6b202043d2b3c4db3f4ebefb06f2df12"

# Bot token from @BotFather
BOT_TOKEN = "7964387907:AAHBMgRfy0Un3hHIdFbOcQl7NyVzYyCkJd0"

EMAIL_SENDER = "bhabyaprakash01@gmail.com"
EMAIL_PASSWORD = "zudlkntnqcnlitbh"

# MongoDB connection string
MONGO_DB_URI = "mongodb+srv://Combobot:Combobot@combobot.4jbtg.mongodb.net/?retryWrites=true&w=majority&appName=Combobot"

# --------------start.py-------------

START_VIDEO = "https://unitedcamps.in/Images/file_5250.jpg"
HELP_MENU_VIDEO = "https://unitedcamps.in/Images/file_5251.jpg"
HELP_VIDEO_1 = "https://unitedcamps.in/Images/file_5251.jpg"
HELP_VIDEO_2 = "https://unitedcamps.in/Images/file_11452.jpg"
HELP_VIDEO_3 = "https://unitedcamps.in/Images/file_11453.jpg"
HELP_VIDEO_4 = "https://unitedcamps.in/Images/file_11454.jpg"

#------------------------------------

LOGGER_ID = -1002059639505
STATS_VIDEO = "https://unitedcamps.in/Images/file_5250.jpg"
OWNER_ID = 7394132959

# Heroku deployment
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

# GitHub repo
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/Roninbyrne/Scott-bot")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "master")
GIT_TOKEN = getenv("git_token", None)

# Support
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/PacificArc")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/phoenixXsupport")

# Validate URLs
if SUPPORT_CHANNEL:
    if not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
        raise SystemExit("[ERROR] - Your SUPPORT_CHANNEL url is wrong. Please ensure that it starts with https://")

if SUPPORT_CHAT:
    if not re.match(r"(?:http|https)://", SUPPORT_CHAT):
        raise SystemExit("[ERROR] - Your SUPPORT_CHAT url is wrong. Please ensure that it starts with https://")


# ============ EMAIL HTML TEMPLATES ============

EMAIL_SUBJECT_OTP = "One Time Verification from Team Scott"
EMAIL_SUBJECT_FINAL = "Your Registration Details from Team Scott"

EMAIL_BODY_OTP = """
<html>
  <body style="font-family: Arial, sans-serif; background-color:#f9f9f9; padding:20px;">
    <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
      <h2 style="color:#2E8B57;">🔐 OTP Verification</h2>
      <p>Hello,</p>
      <p>You requested an OTP for verification. Please use the following code to continue your registration:</p>

      <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; text-align: center;">
        <p style="font-size: 20px;"><b>🔑 Your OTP is:</b></p>
        <p style="font-size: 28px; color: #2E8B57;"><code>{otp}</code></p>
      </div>

      <p>This OTP is valid for <b>5 minutes</b>. Please do not share it with anyone.</p>

      <p>Thank you for choosing Team Scott!</p>
      <p style="color: #555;">Best regards,<br><b>Team Scott</b></p>
    </div>
  </body>
</html>
"""

EMAIL_BODY_FINAL = """
<html>
  <body style="font-family: Arial, sans-serif; background-color:#f9f9f9; padding:20px;">
    <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
      <h2 style="color:#2E8B57;">🎉 Registration Successful</h2>
      <p>Hello,</p>
      <p>Your registration has been completed successfully. Below are your credentials and channel details:</p>

      <ul style="list-style-type: none; padding: 0;">
        <li><b>🆔 Login ID:</b> <code>{login_id}</code></li>
        <li><b>🔑 Password:</b> <code>{password}</code></li>
        <li><b>🔒 Private Channel:</b> {private_name} (<code>{private_id}</code>)</li>
        <li><b>📢 Public Channel:</b> {public_name} (<code>{public_id}</code>)</li>
      </ul>

      <p>Keep this information safe and secure. Do not share it with anyone.</p>

      <p style="color: #555;">Best regards,<br><b>Team Scott</b></p>
    </div>
  </body>
</html>
"""

EMAIL_SUBJECT_DELETE_OTP = "⚠️ Confirm Your Account Deletion - Team Scott"
EMAIL_BODY_DELETE_OTP = """
<html>
  <body style="font-family: Arial, sans-serif; background-color:#fff3f3; padding:20px;">
    <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(255,0,0,0.1);">
      <h2 style="color:#cc0000;">⚠️ Account Deletion Request</h2>
      <p>You have requested to <b>permanently delete</b> your account data associated with our Telegram bot.</p>
      <p>To confirm this request, please use the following OTP:</p>

      <div style="background-color: #fff0f0; padding: 15px; border-radius: 8px; text-align: center;">
        <p style="font-size: 20px;"><b>🔐 OTP:</b></p>
        <p style="font-size: 28px; color: #cc0000;"><code>{otp}</code></p>
      </div>

      <p>This OTP is valid for <b>5 minutes</b>.</p>
      <p><b>Warning:</b> Once confirmed, all your saved credentials, login ID, email, and associated channel data will be <span style="color: red;">permanently removed</span> from our system. This action <b>cannot be undone</b>.</p>

      <p>If you did not make this request, simply ignore this email and your data will remain safe.</p>

      <p style="color: #555;">Regards,<br><b>Team Scott</b></p>
    </div>
  </body>
</html>
"""

EMAIL_SUBJECT_DELETE_FINAL = "✅ Account Successfully Deleted - Team Scott"
EMAIL_BODY_DELETE_FINAL = """
<html>
  <body style="font-family: Arial, sans-serif; background-color:#f9fff9; padding:20px;">
    <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,128,0,0.1);">
      <h2 style="color: #2e8b57;">✅ Account Deletion Successful</h2>
      <p>Hello,</p>
      <p>Your account associated with the following login ID has been <b>permanently deleted</b> from our system:</p>

      <p><b>🆔 Login ID:</b> <code>{login_id}</code></p>

      <p>All stored credentials, email information, and linked channel data have been removed successfully.</p>

      <p>We’re sorry to see you go. You’re always welcome to join again anytime in the future.</p>

      <p style="color: #555;">Goodbye for now,<br><b>Team Scott</b></p>
    </div>
  </body>
</html>
"""