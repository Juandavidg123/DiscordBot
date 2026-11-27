import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
    HF_TOKEN = os.getenv("HF_TOKEN")

    COMMAND_PREFIX = "pana"

    WEBSERVER_HOST = "0.0.0.0"
    WEBSERVER_PORT = 8000

    COOKIES_FILE = os.getenv("COOKIES_FILE", "cookiesYT.txt")

    # Lavalink configuration
    LAVALINK_URI = os.getenv("LAVALINK_URI", "http://lavalink.jirayu.net:13592")
    LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

    # Twitch configuration
    TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
    TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
    TWITCH_CHANNEL_NAME = os.getenv("TWITCH_CHANNEL_NAME")
    TWITCH_DISCORD_CHANNEL_ID = (
        int(os.getenv("TWITCH_DISCORD_CHANNEL_ID"))
        if os.getenv("TWITCH_DISCORD_CHANNEL_ID") and os.getenv("TWITCH_DISCORD_CHANNEL_ID").isdigit()
        else None
    )
    TWITCH_MENTION = os.getenv("TWITCH_MENTION", "everyone")
    TWITCH_CHECK_INTERVAL = int(os.getenv("TWITCH_CHECK_INTERVAL", "60"))

    MAX_MESSAGE_LENGTH = 2000
    MAX_PING_COUNT = 10
