from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from models.models import User, Message
from datetime import datetime
import logging
from config import BEIFEN_CHAT_ID

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    help_text = """
欢迎使用消息备份机器人！

可用命令：
/start      - 显示此帮助信息
/register   - 注册
/unregister - 注销
/search     - 搜索已备份的消息
/me         - 查看个人信息统计

使用方法：
1. 将想要备份的消息转发给我
2. 使用 /search 命令搜索已备份的消息
"""
    await update.message.reply_text(help_text)


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /register 命令"""
    sessionmaker = context.bot_data["db_session"]
    user = update.effective_user

    with sessionmaker.begin() as session:
        # 检查用户是否已注册
        result = session.execute(
            select(User).where(User.telegram_id == user.id)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            await update.message.reply_text("✅ 您已经注册过了！")
            return

        # 创建新用户
        new_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            photo_url=None,
            registered_at=datetime.now()
        )
        session.add(new_user)

    await update.message.reply_text("✅ 注册成功！")


async def unregister_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /unregister 命令"""
    sessionmaker = context.bot_data["db_session"]
    user = update.effective_user

    try:
        with sessionmaker.begin() as session:
            # 检查用户是否已注册
            result = session.execute(
                select(User).where(User.telegram_id == user.id)
            )
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                await update.message.reply_text("❌ 您还没有注册！")
                return

            # 获取用户的所有备份消息
            messages_result = session.execute(
                select(Message).where(Message.user_id == user.id)
            )
            messages = messages_result.scalars().all()

            # 删除频道中的消息
            deleted_count = 0
            failed_count = 0
            if BEIFEN_CHAT_ID:
                for msg in messages:
                    if msg.forwarded_message_id:
                        try:
                            await context.bot.delete_message(
                                chat_id=BEIFEN_CHAT_ID,
                                message_id=msg.forwarded_message_id
                            )
                            deleted_count += 1
                        except Exception as e:
                            logger.warning(f"删除频道消息失败 (message_id: {msg.forwarded_message_id}): {e}")
                            failed_count += 1

            # 删除用户的所有备份消息
            session.execute(
                delete(Message).where(Message.user_id == user.id)
            )

            # 删除用户
            session.delete(existing_user)

        # 发送注销成功消息
        status_text = f"✅ 注销成功！\n\n"
        status_text += f"📊 统计信息：\n"
        status_text += f"- 总备份消息数：{len(messages)}\n"
        if BEIFEN_CHAT_ID:
            status_text += f"- 频道消息删除：{deleted_count} 成功，{failed_count} 失败\n"

        await update.message.reply_text(status_text)
        logger.info(f"用户 {user.id} 注销成功，删除了 {len(messages)} 条备份消息")

    except Exception as e:
        error_msg = f"❌ 注销过程中发生错误：{str(e)}"
        logger.error(f"用户 {user.id} 注销失败：{str(e)}")
        await update.message.reply_text(error_msg)


async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /me 命令，显示用户信息和消息统计"""
    sessionmaker = context.bot_data["db_session"]
    user = update.effective_user

    with sessionmaker.begin() as session:
        # 检查用户是否已注册
        result = session.execute(
            select(User).where(User.telegram_id == user.id)
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            await update.message.reply_text("❌ 您还没有注册！请先使用 /register 命令注册。")
            return

        # 获取消息统计
        total_count = session.execute(
            select(func.count(Message.id)).where(Message.user_id == user.id)
        ).scalar()

        # 获取各类型消息数量
        type_counts = {}
        for msg_type in ["text", "photo", "video", "document", "voice"]:
            count = session.execute(
                select(func.count(Message.id))
                .where(Message.user_id == user.id)
                .where(Message.message_type == msg_type)
            ).scalar()
            type_counts[msg_type] = count

        # 获取最早和最新的消息时间
        first_message = session.execute(
            select(Message)
            .where(Message.user_id == user.id)
            .order_by(Message.created_at.asc())
            .limit(1)
        ).scalar_one_or_none()

        last_message = session.execute(
            select(Message)
            .where(Message.user_id == user.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

    # 构建用户信息显示
    user_info = f"👤 <b>用户信息</b>\n"
    user_info += f"├ ID: <code>{user.id}</code>\n"
    user_info += f"├ 用户名: {f'@{user.username}' if user.username else '未设置'}\n"
    user_info += f"└ 注册时间: <code>{existing_user.registered_at.strftime('%Y-%m-%d %H:%M:%S')}</code>\n\n"

    # 构建消息统计
    stats = f"📊 <b>消息统计</b>\n"

    # 消息类型映射和图标
    type_info = {
        "text": ("文本消息", "📝"),
        "photo": ("图片消息", "🖼"),
        "video": ("视频消息", "🎥"),
        "document": ("文档消息", "📄"),
        "voice": ("语音消息", "🎤")
    }

    # 添加各类型统计
    for msg_type, count in type_counts.items():
        name, icon = type_info.get(msg_type, (msg_type, "📄"))
        if msg_type == list(type_counts.keys())[-1]:  # 最后一项
            prefix = "└"
        else:
            prefix = "├"
        stats += f"{prefix} {icon} {name}: <code>{count}</code>\n"

    # 添加总计
    stats += f"\n<b>总计消息数</b>: <code>{total_count}</code>\n\n"

    # 添加时间范围信息
    if first_message and last_message:
        time_range = "⏰ <b>时间范围</b>\n"
        time_range += f"├ 最早消息: <code>{first_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
        time_range += f"└ 最新消息: <code>{last_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}</code>"
    else:
        time_range = "⏰ <b>时间范围</b>\n└ 暂无消息记录"

    # 发送统计信息
    await update.message.reply_text(
        f"{user_info}{stats}{time_range}",
        parse_mode='HTML'
    )
