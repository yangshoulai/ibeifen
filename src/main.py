import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN, DATABASE_URL, PROXY
from models.base import init_db
from handlers.command_handlers import start_command, register_command, unregister_command, me_command
from handlers.message_handlers import handle_message
from handlers.search_handlers import search_command, handle_message_view, handle_page_navigation, handle_message_delete

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.application = None
        self.engine = None

    def stop(self):
        """优雅地停止应用程序"""
        logger.info("正在停止机器人...")

        try:
            if self.application:
                self.application.stop()
                self.application.shutdown()

            if self.engine:
                self.engine.dispose()
        except Exception as e:
            logger.error(f"停止时发生错误: {e}")

    def start(self):
        """启动机器人"""
        try:
            # 初始化数据库
            self.engine, session_maker = init_db(DATABASE_URL)

            # 创建应用
            builder = Application.builder().token(BOT_TOKEN)

            # 设置更新器选项
            builder.get_updates_connection_pool_size(10)  # 连接池大小
            builder.get_updates_pool_timeout(15.0)      # 连接超时时间
            builder.get_updates_read_timeout(15.0)         # 读取超时时间
            builder.get_updates_write_timeout(15.0)        # 写入超时时间
            builder.get_updates_connect_timeout(15.0)
            builder.proxy(PROXY if PROXY else None)
            builder.get_updates_proxy(PROXY if PROXY else None)

            self.application = builder.build()

            # 存储数据库会话工厂和引擎
            self.application.bot_data["db_session"] = session_maker
            self.application.bot_data["engine"] = self.engine

            # 注册命令处理程序
            self.application.add_handler(CommandHandler("start", start_command))
            self.application.add_handler(CommandHandler("register", register_command))
            self.application.add_handler(CommandHandler("unregister", unregister_command))
            self.application.add_handler(CommandHandler("search", search_command))
            self.application.add_handler(CommandHandler("me", me_command))

            # 注册消息查看回调处理程序
            self.application.add_handler(CallbackQueryHandler(
                handle_message_view, pattern=r"^view_\d+$"))

            # 注册分页导航回调处理程序
            self.application.add_handler(CallbackQueryHandler(
                handle_page_navigation, pattern=r"^page_\d+$"))

            # 注册消息删除回调处理程序
            self.application.add_handler(CallbackQueryHandler(
                handle_message_delete, pattern=r"^delete_\d+$"))

            # 注册消息处理程序
            self.application.add_handler(MessageHandler(
                filters.TEXT | filters.PHOTO | filters.VIDEO | filters.ATTACHMENT | filters.VOICE,
                handle_message
            ))

            # 启动机器人
            self.application.initialize()
            self.application.start()

            logger.info("机器人已启动，按 Ctrl+C 停止...")

            # 运行直到收到停止信号
            self.application.run_polling(
                drop_pending_updates=True,
                poll_interval=1.0,
                allowed_updates=[Update.MESSAGE, Update.CALLBACK_QUERY]
            )

        except Exception as e:
            logger.error(f"运行时发生错误: {e}")
            self.stop()


def main():
    """主函数"""
    bot = TelegramBot()
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        bot.stop()
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        bot.stop()
    finally:
        logger.info("程序已停止")


if __name__ == "__main__":
    main()
