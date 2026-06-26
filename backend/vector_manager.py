"""
vector_manager.py — ChromaDB 本地向量库管理

职责：
1. 把 loader.py 切分好的片段向量化并存入本地磁盘
2. 按问题检索最相关的 Top-K 片段
3. 支持按领域标签 (domain) 缩小检索范围
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

DEFAULT_PERSIST_DIR = Path(__file__).resolve().parent / "data" / "chroma"
DEFAULT_COLLECTION_NAME = "techinsight_docs"


class VectorManagerError(Exception):
    """向量库操作失败。"""


class VectorManager:
    def __init__(
        self,
        persist_directory: str | Path = DEFAULT_PERSIST_DIR,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise VectorManagerError(
                "未找到 OPENAI_API_KEY。请在 backend/.env 中配置你的 API Key。"
            )

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings()
        self._store: Chroma | None = None

    @property
    def store(self) -> Chroma:
        """懒加载 Chroma 实例，复用同一个本地集合。"""
        if self._store is None:
            self._store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_directory),
            )
        return self._store

    @staticmethod
    def _normalize_metadata(chunk: Document) -> Document:
        """
        ChromaDB 的 metadata 只支持 str/int/float/bool。
        因此把 domain_tags 列表转成逗号字符串，并提取主领域 domain 供过滤。
        """
        metadata = dict(chunk.metadata)
        raw_tags = metadata.get("domain_tags", [])

        if isinstance(raw_tags, str):
            tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
        elif isinstance(raw_tags, list):
            tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]
        else:
            tags = []

        metadata["domain_tags"] = ",".join(tags)
        metadata["domain"] = tags[0] if tags else "general"

        for key, value in list(metadata.items()):
            if isinstance(value, (dict, list)):
                metadata[key] = str(value)

        chunk.metadata = metadata
        return chunk

    def add_chunks(self, chunks: list[Document]) -> int:
        """向向量库追加文档片段。"""
        if not chunks:
            return 0

        prepared = [self._normalize_metadata(chunk) for chunk in chunks]
        self.store.add_documents(prepared)
        return len(prepared)

    def search(
        self,
        query: str,
        *,
        top_k: int = 4,
        domain: str | None = None,
    ) -> list[Document]:
        """相似度检索，可选按 domain 过滤。"""
        search_kwargs: dict = {"k": top_k}
        if domain:
            search_kwargs["filter"] = {"domain": domain}

        return self.store.similarity_search(query, **search_kwargs)

    def count(self) -> int:
        """当前集合中的文档数量。"""
        return self.store._collection.count()


def ingest_file(
    file_path: str | Path,
    *,
    domain_tags: list[str] | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    manager: VectorManager | None = None,
) -> int:
    """便捷方法：加载文件 -> 切分 -> 写入向量库。"""
    from loader import load_and_chunk

    chunks = load_and_chunk(
        file_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        domain_tags=domain_tags,
    )
    vector_manager = manager or VectorManager()
    return vector_manager.add_chunks(chunks)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python vector_manager.py ingest <文件路径> [领域标签]")
        print("  python vector_manager.py search <问题> [领域标签]")
        print("")
        print("示例:")
        print("  python vector_manager.py ingest ~/Desktop/X.pdf 后端")
        print('  python vector_manager.py search "项目技术栈是什么" 后端')
        sys.exit(1)

    command = sys.argv[1]

    try:
        manager = VectorManager()

        if command == "ingest":
            if len(sys.argv) < 3:
                print("请提供文件路径")
                sys.exit(1)

            file_path = sys.argv[2]
            tags = [sys.argv[3]] if len(sys.argv) > 3 else ["general"]
            added = ingest_file(file_path, domain_tags=tags, manager=manager)
            print(f"入库成功: {added} 个片段")
            print(f"当前库内总数: {manager.count()}")

        elif command == "search":
            if len(sys.argv) < 3:
                print("请提供检索问题")
                sys.exit(1)

            question = sys.argv[2]
            domain = sys.argv[3] if len(sys.argv) > 3 else None
            results = manager.search(question, top_k=3, domain=domain)
            print(f"命中 {len(results)} 条结果")
            for index, doc in enumerate(results, start=1):
                print("-" * 40)
                print(
                    f"[{index}] {doc.metadata.get('source_file')} | "
                    f"page={doc.metadata.get('page_index')}"
                )
                print(doc.page_content[:200])

        else:
            print(f"未知命令: {command}")
            sys.exit(1)

    except VectorManagerError as exc:
        print(f"错误: {exc}")
        sys.exit(1)
