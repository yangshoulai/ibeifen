
from telegram import Message, Update
from telegram.ext import ContextTypes
import asyncio


async def reply_and_delete_message(text: str, update: Update, context: ContextTypes.DEFAULT_TYPE, delete: bool = True,  wait_seconds: int = 2) -> None:
    """Delete the message that was sent by the user."""
    msg = await update.message.reply_text(text)
    if delete:
        await asyncio.sleep(wait_seconds)
        await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)


async def delete_message(message: Message, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
