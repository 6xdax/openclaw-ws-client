"""配置"""
import os
from dotenv import load_dotenv

load_dotenv()

GATEWAY_URL = "ws://127.0.0.1:18789"
TOKEN = os.environ.get("OPENCLAW_TOKEN", "")
LOCALE = "zh-CN"
CLIENT_ID = "cli"
CLIENT_VERSION = "1.0.0"
PLATFORM = "linux"
