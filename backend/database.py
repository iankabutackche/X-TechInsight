"""
database.py — SQLite 数据库模型

职责：
1. 定义 Chats / Messages 两张核心表
2. 提供数据库初始化与 Session 获取
3. 为第二阶段 FastAPI 接口提供数据层基础
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "app.db"


class Base(DeclarativeBase):
    pass


class Chat(Base):
    """对话空间：每个 ChatID 对应独立上下文。"""

    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tag: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
    )


class Message(Base):
    """对话消息：按 ChatID 隔离存储。"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    chat: Mapped["Chat"] = relationship(back_populates="messages")


def get_engine(db_path: str | Path = DEFAULT_DB_PATH):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", echo=False, future=True)


def get_session_factory(db_path: str | Path = DEFAULT_DB_PATH):
    engine = get_engine(db_path)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """创建数据库表（若不存在）。"""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


def create_chat(session: Session, *, name: str, tag: str = "general") -> Chat:
    chat = Chat(name=name, tag=tag)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


def update_chat(
    session: Session,
    chat_id: str,
    *,
    name: str | None = None,
    tag: str | None = None,
) -> Chat | None:
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        return None

    if name is not None:
        chat.name = name
    if tag is not None:
        chat.tag = tag

    session.commit()
    session.refresh(chat)
    return chat


def add_message(session: Session, *, chat_id: str, role: str, content: str) -> Message:
    message = Message(chat_id=chat_id, role=role, content=content)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def list_chats(session: Session) -> list[Chat]:
    return session.query(Chat).order_by(Chat.created_at.desc()).all()


def get_chat_messages(session: Session, chat_id: str) -> list[Message]:
    return (
        session.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )


if __name__ == "__main__":
    init_db()
    SessionLocal = get_session_factory()

    with SessionLocal() as session:
        demo_chat = create_chat(session, name="技术栈讨论", tag="后端")
        add_message(
            session,
            chat_id=demo_chat.id,
            role="user",
            content="这个项目用了哪些技术栈？",
        )
        add_message(
            session,
            chat_id=demo_chat.id,
            role="assistant",
            content="React、FastAPI、LangChain、ChromaDB、SQLite。",
        )

        chats = list_chats(session)
        print(f"数据库初始化成功: {DEFAULT_DB_PATH}")
        print(f"当前对话数量: {len(chats)}")
        print(f"示例 ChatID: {demo_chat.id}")
        print(f"示例消息数: {len(get_chat_messages(session, demo_chat.id))}")
