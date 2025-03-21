from pathlib import Path
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def init_db(database_url: str):
    """初始化数据库"""
    # 确保数据库目录存在
    db_path = Path(database_url.replace('sqlite:///', ''))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建引擎
    engine = create_engine(
        database_url.replace('sqlite+aiosqlite', 'sqlite'),
        echo=False,
        pool_pre_ping=True,
    )

    # 创建表
    Base.metadata.create_all(engine)

    # 创建会话工厂
    session_maker = sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False
    )

    return engine, session_maker
