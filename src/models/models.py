from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from models.base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    photo_url = Column(String(500))
    registered_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    chat_id = Column(Integer, nullable=False)
    message_type = Column(String(50), nullable=False)
    text = Column(Text)
    tokens = Column(Text)  # 分词后的文本，以空格分隔
    file_id = Column(String(255))  # 如果是媒体消息，存储文件ID
    forwarded_message_id = Column(Integer)  # 转发到目标群组后的消息ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Message(id={self.id}, user_id={self.user_id})>" 