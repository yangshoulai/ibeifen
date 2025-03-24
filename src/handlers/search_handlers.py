import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, or_, func
from models.models import Message
from config import MESSAGES_PER_PAGE, BEIFEN_CHAT_ID
from utils import bot_utils
from utils.text_utils import tokenize_text
logger = logging.getLogger(__name__)
# 会话状态
SEARCHING = 1


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /search 命令

    用法：/search [关键词]
    示例：
        /search          # 显示最近的消息
        /search 关键词   # 搜索包含关键词的消息
    """
    # 获取页码，默认为第1页
    page = 1

    # 保存搜索词到 context
    query = " ".join(context.args) if context.args else ""
    context.user_data['search_query'] = query

    await show_search_results(update, context, page, query, is_new_search=True)


async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int, query: str, is_new_search: bool = False):
    """显示搜索结果的分页内容"""
    sessionmaker = context.bot_data["db_session"]
    user_id = update.effective_user.id if is_new_search else update.callback_query.from_user.id

    # 构建基础查询
    stmt = select(Message).where(Message.user_id == user_id)

    # 如果有搜索关键词，添加关键词过滤
    if query:
        search_tokens = tokenize_text(query)
        search_words = search_tokens.split()
        conditions = []
        for word in search_words:
            conditions.append(Message.tokens.contains(word))
        stmt = stmt.where(or_(*conditions))

    # 计算总记录数
    with sessionmaker.begin() as session:
        count_stmt = select(func.count()).select_from(stmt)
        total_count = session.execute(count_stmt).scalar()

        # 计算总页数
        total_pages = (total_count + MESSAGES_PER_PAGE - 1) // MESSAGES_PER_PAGE

        # 确保页码在有效范围内
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1

        # 添加分页
        offset = (page - 1) * MESSAGES_PER_PAGE
        stmt = stmt.order_by(Message.created_at.desc())
        stmt = stmt.offset(offset).limit(MESSAGES_PER_PAGE)

        # 执行查询
        result = session.execute(stmt)
        messages = result.scalars().all()

    if not messages:
        text = "未找到任何消息！" if not query else f"未找到包含关键词 '{query}' 的消息！"
        if is_new_search:
            await update.message.reply_text(text)
        else:
            await update.callback_query.edit_message_text(text)
        return

    # 消息类型图标映射
    type_icons = {
        "text": "📝",
        "photo": "🖼",
        "video": "🎥",
        "document": "📄",
        "voice": "🎤"
    }

    def clean_message_text(text: str, max_length: int = 100) -> str:
        """清理和格式化消息文本"""
        if not text:
            return "无文本内容"

        # 替换换行符为空格
        text = text.replace('\n', ' ').replace('\r', '')
        # 移除多余的空格
        text = ' '.join(text.split())

        if len(text) > max_length:
            # 确保不会在表情符号中间截断
            truncated = text[:max_length]
            # 找到最后一个完整的表情符号
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:  # 如果找到的空格位置在合理范围内
                truncated = truncated[:last_space]
            return truncated + "..."

        return text

    # 构建搜索结果显示
    title = "最近的消息" if not query else f'搜索 "{query}"'
    text = f"<b>{title}</b> (第 {page}/{total_pages} 页)\n\n"

    # 添加消息列表
    for idx, msg in enumerate(messages, 1):
        # 获取消息类型图标
        icon = type_icons.get(msg.message_type, "📄")

        # 格式化时间
        time_str = msg.created_at.strftime("%Y-%m-%d %H:%M")

        # 处理消息预览
        preview = clean_message_text(msg.text)

        # 构建消息条目
        text += f"{idx}. {icon} <code>{time_str}</code>\n"
        if msg.message_type != "text":
            text += f"   └ 类型：{msg.message_type}\n"
        text += f"   └ {preview}\n\n"

    # 构建按钮
    keyboard = []
    current_row = []

    # 添加序号按钮和删除按钮，每行最多5个
    for idx, msg in enumerate(messages, 1):
        # 创建包含查看和删除按钮的行
        row = [
            InlineKeyboardButton(f"查看 {idx}", callback_data=f"view_{msg.id}"),
            InlineKeyboardButton(f"删除 {idx}", callback_data=f"delete_{msg.id}")
        ]
        keyboard.append(row)

    # 添加分页按钮
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"page_{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if is_new_search:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"发送搜索结果失败: {e}")
        error_text = "❌ 消息包含不支持的格式，请尝试其他搜索条件。"
        if is_new_search:
            await update.message.reply_text(error_text)
        else:
            await update.callback_query.edit_message_text(error_text)


async def handle_page_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理分页导航"""
    query = update.callback_query
    await query.answer()

    # 获取目标页码
    page = int(query.data.split('_')[1])

    # 获取之前保存的搜索查询
    search_query = context.user_data.get('search_query', '')

    # 显示对应页的搜索结果
    await show_search_results(update, context, page, search_query, is_new_search=False)


async def handle_message_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理消息查看回调"""
    query = update.callback_query
    await query.answer()

    message_id = int(query.data.split('_')[1])
    sessionmaker = context.bot_data["db_session"]

    with sessionmaker.begin() as session:
        result = session.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            await query.message.reply_text("❌ 消息不存在！")
            return

        try:
            # 如果配置了目标群组，尝试从群组转发消息
            if BEIFEN_CHAT_ID and message.forwarded_message_id:
                try:
                    # 尝试从频道转发消息
                    await context.bot.forward_message(
                        chat_id=update.effective_user.id,
                        from_chat_id=BEIFEN_CHAT_ID,
                        message_id=message.forwarded_message_id
                    )
                    return
                except Exception as e:
                    logger.warning(f"从频道转发消息失败: {e}，将使用备份的消息内容")

            # 如果从频道转发失败或没有配置频道，使用备份的消息内容
            if message.message_type == "text":
                await query.message.reply_text(message.text)
            elif message.file_id:
                caption = message.text if message.text else None
                if message.message_type == "photo":
                    await query.message.reply_photo(message.file_id, caption=caption)
                elif message.message_type == "video":
                    await query.message.reply_video(message.file_id, caption=caption)
                elif message.message_type == "document":
                    await query.message.reply_document(message.file_id, caption=caption)
                elif message.message_type == "voice":
                    await query.message.reply_voice(message.file_id, caption=caption)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            await query.message.reply_text("❌ 消息发送失败，请稍后重试。")


async def handle_message_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理消息删除回调"""
    query = update.callback_query
    await query.answer()

    message_id = int(query.data.split('_')[1])
    sessionmaker = context.bot_data["db_session"]

    try:
        with sessionmaker.begin() as session:
            # 获取消息信息
            result = session.execute(
                select(Message).where(Message.id == message_id)
            )
            message = result.scalar_one_or_none()

            if not message:
                await query.message.reply_text("❌ 消息不存在！")
                return

            # 如果配置了目标群组，尝试删除群组中的消息
            if BEIFEN_CHAT_ID and message.forwarded_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=BEIFEN_CHAT_ID,
                        message_id=message.forwarded_message_id
                    )
                except Exception as e:
                    logger.warning(f"删除频道消息失败: {e}")

            # 删除数据库中的消息记录
            session.delete(message)

        # 发送删除成功消息
        m = await query.message.reply_text("✅ 消息已删除！")

        # 刷新搜索结果
        search_query = context.user_data.get('search_query', '')
        current_page = int(query.message.text.split('第 ')[1].split('/')[0])
        await show_search_results(update, context, current_page, search_query, is_new_search=False)

        await bot_utils.delete_message(m, context)

    except Exception as e:
        logger.error(f"删除消息失败: {e}")
        await query.message.reply_text("❌ 删除消息失败，请稍后重试。")
