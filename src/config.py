import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/bot.db')

# 目标群组ID
BEIFEN_CHAT_ID = int(os.getenv('BEIFEN_CHAT_ID', 0))

# 每页显示的消息数量
MESSAGES_PER_PAGE = 10 

PROXY=os.getenv('PROXY', '')