from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import User, Message
from utils.text_utils import tokenize_text
from config import BEIFEN_CHAT_ID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理转发的消息"""
    sessionmaker = context.bot_data["db_session"]
    user = update.effective_user
    message = update.message

    # 检查用户是否已注册
    with sessionmaker.begin() as session:
        result = session.execute(select(User).where(User.telegram_id == user.id))
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            # 自动注册用户
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                photo_url=None,
                registered_at=datetime.utcnow()
            )
            session.add(new_user)
            await update.message.reply_text("✅ 您已被自动注册！")

    # 确定消息类型和内容
    message_type = "text"
    text = message.text
    file_id = None

    if message.photo:
        message_type = "photo"
        text = message.caption
        file_id = message.photo[-1].file_id
    elif message.video:
        message_type = "video"
        text = message.caption
        file_id = message.video.file_id
    elif message.document:
        message_type = "document"
        text = message.caption
        file_id = message.document.file_id
    elif message.voice:
        message_type = "voice"
        text = message.caption
        file_id = message.voice.file_id

    # 对文本进行分词
    tokens = tokenize_text(text) if text else ""

    # 转发消息到目标群组
    forwarded_message_id = None
    if BEIFEN_CHAT_ID:
        try:
            forwarded_message = await message.forward(BEIFEN_CHAT_ID)
            forwarded_message_id = forwarded_message.message_id
        except Exception as e:
            logger.error(f"消息转发失败：{str(e)}")
            await update.message.reply_text(f"❌ 消息转发失败：{str(e)}")
            return

    # 保存消息
    with sessionmaker.begin() as session:
        new_message = Message(
            message_id=message.message_id,
            user_id=user.id,
            chat_id=message.chat_id,
            message_type=message_type,
            text=text,
            tokens=tokens,
            file_id=file_id,
            forwarded_message_id=forwarded_message_id,
            created_at=message.date
        )
        session.add(new_message)

    await update.message.reply_text("✅ 消息已备份！")
