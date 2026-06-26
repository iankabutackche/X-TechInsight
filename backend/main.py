"""
main.py — FastAPI 后端入口

当前步骤：
- 启动 Web 服务
- /chats/create 创建对话
- /files/upload 上传文档并在后台解析入库
- /query/stream 流式问答（SSE）
- /chats/list 获取对话列表
- /chats/{chat_id}/messages 获取对话历史
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Generator
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from agent_logic import DEFAULT_TOP_K, SYSTEM_PROMPT, AgentLogic, AgentLogicError
from database import Chat, add_message, create_chat, get_chat_messages, get_session_factory, init_db, list_chats, update_chat
from loader import EncryptedPDFError, UnsupportedFileError

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent / "data" / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt"}

SessionLocal = get_session_factory()

app = FastAPI(
    title="X-TechInsight API",
    description="模块化全栈 RAG 技术文档分析平台",
    version="0.1.0",
)


class CreateChatRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="对话名称")
    tag: str = Field(default="general", max_length=50, description="领域标签")


class UpdateChatRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100, description="对话名称")
    tag: str | None = Field(default=None, max_length=50, description="领域标签")


class ChatResponse(BaseModel):
    id: str
    name: str
    tag: str


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    tag: str
    status: str
    message: str


class QueryRequest(BaseModel):
    chat_id: str = Field(..., description="对话 ID")
    question: str = Field(..., min_length=1, description="用户问题")


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sse_event(event: str, data: dict | list) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def build_history_block(messages: list) -> str:
    if not messages:
        return "（无历史对话）"

    lines = [f"{message.role}: {message.content}" for message in messages]
    return "\n".join(lines)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def process_uploaded_file(file_path: Path, domain_tags: list[str]) -> None:
    """后台任务：解析文件并写入向量库。"""
    from vector_manager import ingest_file

    try:
        chunk_count = ingest_file(file_path, domain_tags=domain_tags)
        logger.info("文件入库成功: %s, 片段数=%s", file_path.name, chunk_count)
    except EncryptedPDFError as exc:
        logger.error("加密 PDF 无法解析: %s", exc)
    except UnsupportedFileError as exc:
        logger.error("不支持的文件格式: %s", exc)
    except Exception as exc:
        logger.exception("文件入库失败: %s", exc)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chats/create", response_model=ChatResponse)
def create_chat_endpoint(
    payload: CreateChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """创建一个新的对话空间。"""
    name = payload.name.strip()
    tag = payload.tag.strip() or "general"

    if not name:
        raise HTTPException(status_code=400, detail="对话名称不能为空")

    chat: Chat = create_chat(db, name=name, tag=tag)
    return ChatResponse(id=chat.id, name=chat.name, tag=chat.tag)


@app.get("/chats/list", response_model=list[ChatResponse])
def list_chats_endpoint(db: Session = Depends(get_db)) -> list[ChatResponse]:
    """获取所有对话列表。"""
    chats = list_chats(db)
    return [ChatResponse(id=chat.id, name=chat.name, tag=chat.tag) for chat in chats]


@app.get("/chats/{chat_id}/messages", response_model=list[MessageResponse])
def get_chat_messages_endpoint(
    chat_id: str,
    db: Session = Depends(get_db),
) -> list[MessageResponse]:
    """获取指定对话的历史消息。"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = get_chat_messages(db, chat_id)
    return [
        MessageResponse(id=message.id, role=message.role, content=message.content)
        for message in messages
    ]


@app.patch("/chats/{chat_id}", response_model=ChatResponse)
def update_chat_endpoint(
    chat_id: str,
    payload: UpdateChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """更新对话名称或领域标签。"""
    name = payload.name.strip() if payload.name else None
    tag = payload.tag.strip() if payload.tag else None

    if name == "":
        raise HTTPException(status_code=400, detail="对话名称不能为空")
    if tag == "":
        tag = "general"

    chat = update_chat(db, chat_id, name=name, tag=tag)
    if not chat:
        raise HTTPException(status_code=404, detail="对话不存在")

    return ChatResponse(id=chat.id, name=chat.name, tag=chat.tag)


@app.post("/files/upload", response_model=UploadResponse)
async def upload_file_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tag: str = Form(default="general"),
) -> UploadResponse:
    """上传文档，后台异步解析并写入向量库。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"暂不支持的格式: {suffix}，仅支持 {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件超过 10MB 上限")

    domain_tag = tag.strip() or "general"
    file_id = str(uuid4())
    safe_name = f"{file_id}{suffix}"
    saved_path = UPLOAD_DIR / safe_name
    saved_path.write_bytes(content)

    background_tasks.add_task(process_uploaded_file, saved_path, [domain_tag])

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        tag=domain_tag,
        status="processing",
        message="文件已接收，正在后台解析入库",
    )


@app.post("/query/stream")
def query_stream_endpoint(
    payload: QueryRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """流式问答：读取对话历史 + 向量检索 + SSE 返回。"""
    chat = db.query(Chat).filter(Chat.id == payload.chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="对话不存在")

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    prior_messages = get_chat_messages(db, payload.chat_id)
    history_block = build_history_block(prior_messages)
    add_message(db, chat_id=chat.id, role="user", content=question)

    try:
        agent = AgentLogic()
    except AgentLogicError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    documents = agent.vector_manager.search(
        question,
        top_k=DEFAULT_TOP_K,
        domain=chat.tag,
    )
    context_block, citations = AgentLogic._build_context_block(documents)

    def stream_answer() -> Generator[str, None, None]:
        if not documents:
            fallback = "根据现有资料，我无法回答这个问题。"
            yield sse_event("token", {"content": fallback})
            with SessionLocal() as session:
                add_message(session, chat_id=chat.id, role="assistant", content=fallback)
            yield sse_event("sources", [])
            yield sse_event("done", {})
            return

        user_prompt = f"""历史对话：
{history_block}

参考片段：
{context_block}

用户问题：
{question}

请基于参考片段回答。无法从片段中得到答案时，必须明确说明无法回答。"""

        chunks: list[str] = []
        try:
            for chunk in agent.llm.stream(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt),
                ]
            ):
                token = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                if not token:
                    continue
                chunks.append(token)
                yield sse_event("token", {"content": token})
        except Exception as exc:
            yield sse_event("error", {"message": f"生成回答失败: {exc}"})
            return

        full_answer = "".join(chunks).strip()
        with SessionLocal() as session:
            add_message(session, chat_id=chat.id, role="assistant", content=full_answer)

        sources_payload = [
            {
                "index": source.index,
                "source_file": source.source_file,
                "page_index": source.page_index,
                "excerpt": source.excerpt,
            }
            for source in citations
        ]
        yield sse_event("sources", sources_payload)
        yield sse_event("done", {})

    return StreamingResponse(stream_answer(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
