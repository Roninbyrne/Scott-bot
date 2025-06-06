
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI
from ..logging import LOGGER

logger = LOGGER(__name__)

logger.info("Connecting to your Mongo Database...")

try:
    mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
    db = mongo_client["store"]

    group_log_db = db["group_logs"]
    global_userinfo_db = db["user_info"]
    register_data_db = db["register_data"]
    session_db = db["session_data"]
    user_states_collection = db["user_states"]
    video_channels_collection = db["video_channels"]
    mongodb = db

    logger.info("Connected to your Mongo Database.")
except Exception as e:
    logger.error(f"Failed to connect to your Mongo Database: {e}")
    exit()