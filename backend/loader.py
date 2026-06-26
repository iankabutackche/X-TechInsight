"""
loader.py — 文档加载与切分

职责：
1. 读取 .pdf / .md / .txt 文件
2. 识别加密 PDF 并给出友好提示
3. 按项目规格切分文本，并注入元数据
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


class EncryptedPDFError(Exception):
    """加密 PDF，无法解析。"""


class UnsupportedFileError(Exception):
    """不支持的文件格式。"""


def _protect_markdown_code_blocks(text: str) -> str:
    """
    在 Markdown 代码块前后插入占位分隔符，
    降低 RecursiveCharacterTextSplitter 把代码块从中间切断的概率。
    """
    lines = text.splitlines(keepends=True)
    result: list[str] = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_code_block:
                result.append("\n<!-- CODE_BLOCK_START -->\n")
                in_code_block = True
            else:
                result.append(line)
                result.append("\n<!-- CODE_BLOCK_END -->\n")
                in_code_block = False
                continue
        result.append(line)

    return "".join(result)


def load_document(file_path: str | Path) -> list[Document]:
    """根据文件类型加载文档，返回 LangChain Document 列表。"""
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileError(
            f"暂不支持的格式: {suffix}，目前仅支持 {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if suffix == ".pdf":
        try:
            loader = PyPDFLoader(str(path))
            documents = loader.load()
        except Exception as exc:
            message = str(exc).lower()
            if "encrypted" in message or "password" in message:
                raise EncryptedPDFError(
                    f"检测到加密 PDF，无法解析: {path.name}。请上传未加密的 PDF。"
                ) from exc
            raise
    else:
        documents = TextLoader(str(path), encoding="utf-8").load()

    upload_time = datetime.now(timezone.utc).isoformat()
    for doc in documents:
        doc.metadata.setdefault("source_file", path.name)
        doc.metadata.setdefault("upload_time", upload_time)
        if suffix == ".md":
            doc.page_content = _protect_markdown_code_blocks(doc.page_content)

    return documents


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    domain_tags: list[str] | None = None,
) -> list[Document]:
    """将文档切分为带元数据的文本块。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""],
    )

    tags = domain_tags or []
    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = str(uuid4())
        chunk.metadata["page_index"] = chunk.metadata.get("page", 0)
        chunk.metadata["domain_tags"] = tags

    return chunks


def load_and_chunk(
    file_path: str | Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    domain_tags: list[str] | None = None,
) -> list[Document]:
    """一步到位：加载文件并切分。"""
    documents = load_document(file_path)
    return chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        domain_tags=domain_tags,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python loader.py <文件路径>")
        print("示例: python loader.py ../test.pdf")
        sys.exit(1)

    target = sys.argv[1]
    try:
        pieces = load_and_chunk(target, domain_tags=["测试"])
        print(f"成功切分: {len(pieces)} 个片段")
        print("-" * 40)
        print("第一个片段预览:")
        print(pieces[0].page_content[:300])
        print("-" * 40)
        print("元数据:", pieces[0].metadata)
    except (EncryptedPDFError, UnsupportedFileError, FileNotFoundError) as exc:
        print(f"错误: {exc}")
        sys.exit(1)
