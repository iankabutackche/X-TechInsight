"""
agent_logic.py — RAG 问答逻辑

职责：
1. 从向量库检索相关片段
2. 将片段作为上下文交给大模型生成回答
3. 资料不足时明确说「无法回答」，避免瞎编
4. 返回答案与可溯源的来源列表
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from vector_manager import VectorManager

DEFAULT_TOP_K = 4
DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """你是 X-TechInsight 技术文档分析助手。

必须遵守：
1. 只能根据用户提供的「参考片段」回答，禁止使用片段以外的知识。
2. 若参考片段无法支撑答案，必须明确回复：
   「根据现有资料，我无法回答这个问题。」
3. 每个关键结论后标注 [Source N]（N 为片段编号）。
4. 回答简洁、结构化，适合技术人员阅读。
"""


@dataclass
class SourceCitation:
    index: int
    source_file: str
    page_index: int
    excerpt: str


@dataclass
class AgentResponse:
    question: str
    answer: str
    sources: list[SourceCitation]
    domain: str | None = None


class AgentLogicError(Exception):
    """问答逻辑执行失败。"""


class AgentLogic:
    def __init__(
        self,
        vector_manager: VectorManager | None = None,
        *,
        top_k: int = DEFAULT_TOP_K,
        model: str = DEFAULT_MODEL,
    ) -> None:
        load_dotenv()

        if not os.getenv("OPENAI_API_KEY"):
            raise AgentLogicError(
                "未找到 OPENAI_API_KEY。请在 backend/.env 中配置你的 API Key。"
            )

        self.vector_manager = vector_manager or VectorManager()
        self.top_k = top_k
        self.llm = ChatOpenAI(model=model, temperature=0)

    @staticmethod
    def _build_context_block(documents: list[Document]) -> tuple[str, list[SourceCitation]]:
        """把检索结果格式化为 Prompt 上下文，并生成来源列表。"""
        citations: list[SourceCitation] = []
        blocks: list[str] = []

        for index, doc in enumerate(documents, start=1):
            source_file = str(doc.metadata.get("source_file", "unknown"))
            page_index = int(doc.metadata.get("page_index", doc.metadata.get("page", 0)))
            excerpt = doc.page_content.strip()

            citations.append(
                SourceCitation(
                    index=index,
                    source_file=source_file,
                    page_index=page_index,
                    excerpt=excerpt[:300],
                )
            )
            blocks.append(
                f"[Source {index}] 文件: {source_file} | 页码: {page_index}\n{excerpt}"
            )

        return "\n\n".join(blocks), citations

    def ask(
        self,
        question: str,
        *,
        domain: str | None = None,
        top_k: int | None = None,
    ) -> AgentResponse:
        """检索 + 生成回答。"""
        question = question.strip()
        if not question:
            raise AgentLogicError("问题不能为空。")

        documents = self.vector_manager.search(
            question,
            top_k=top_k or self.top_k,
            domain=domain,
        )

        context_block, citations = self._build_context_block(documents)

        if not documents:
            return AgentResponse(
                question=question,
                answer="根据现有资料，我无法回答这个问题。",
                sources=[],
                domain=domain,
            )

        user_prompt = f"""参考片段：
{context_block}

用户问题：
{question}

请基于参考片段回答。无法从片段中得到答案时，必须明确说明无法回答。"""

        response = self.llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]
        )

        answer = response.content if isinstance(response.content, str) else str(response.content)

        return AgentResponse(
            question=question,
            answer=answer.strip(),
            sources=citations,
            domain=domain,
        )


def format_response(result: AgentResponse) -> str:
    """把回答和来源格式化为终端可读文本。"""
    lines = [
        "=" * 50,
        f"问题: {result.question}",
        f"领域: {result.domain or '未指定'}",
        "=" * 50,
        "",
        result.answer,
        "",
        "-" * 50,
        "来源证据:",
    ]

    if not result.sources:
        lines.append("（无命中来源）")
    else:
        for source in result.sources:
            lines.append(
                f"[Source {source.index}] {source.source_file} | page={source.page_index}"
            )
            lines.append(source.excerpt[:200])
            lines.append("")

    return "\n".join(lines).strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python agent_logic.py <问题> [领域标签]")
        print('示例: python agent_logic.py "项目用了哪些技术栈" 后端')
        sys.exit(1)

    user_question = sys.argv[1]
    user_domain = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        agent = AgentLogic()
        result = agent.ask(user_question, domain=user_domain)
        print(format_response(result))
    except AgentLogicError as exc:
        print(f"错误: {exc}")
        sys.exit(1)
