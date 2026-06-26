"""
eval_test.py — 手动评估不同 Top-K 的检索效果

职责：
1. 对同一个问题，分别用不同的 Top-K 做检索
2. 直观对比「喂给 AI 的片段数量」与「命中质量」
3. 帮助选出合适的 Top-K 默认值
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from vector_manager import VectorManager

DEFAULT_TOP_K_LIST = [1, 2, 4, 6, 8]


@dataclass
class TopKResult:
    top_k: int
    hit_count: int
    previews: list[str]


def _preview_document(doc: Document, max_chars: int = 120) -> str:
    source_file = doc.metadata.get("source_file", "unknown")
    page_index = doc.metadata.get("page_index", doc.metadata.get("page", 0))
    content = doc.page_content.strip().replace("\n", " ")
    if len(content) > max_chars:
        content = content[:max_chars] + "..."
    return f"{source_file} | page={page_index} | {content}"


def evaluate_top_k(
    question: str,
    *,
    domain: str | None = None,
    top_k_list: list[int] | None = None,
    manager: VectorManager | None = None,
) -> list[TopKResult]:
    """对同一问题测试多个 Top-K 值。"""
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空。")

    vector_manager = manager or VectorManager()
    k_values = top_k_list or DEFAULT_TOP_K_LIST
    results: list[TopKResult] = []

    for top_k in k_values:
        documents = vector_manager.search(question, top_k=top_k, domain=domain)
        previews = [_preview_document(doc) for doc in documents]
        results.append(
            TopKResult(
                top_k=top_k,
                hit_count=len(documents),
                previews=previews,
            )
        )

    return results


def format_eval_report(
    question: str,
    results: list[TopKResult],
    *,
    domain: str | None = None,
) -> str:
    """格式化终端输出报告。"""
    lines = [
        "=" * 60,
        f"评估问题: {question}",
        f"领域过滤: {domain or '未指定'}",
        "=" * 60,
        "",
        "阅读建议:",
        "- 看每个 Top-K 下命中的片段是否「真的相关」",
        "- Top-K 太小：可能漏掉关键信息",
        "- Top-K 太大：可能引入噪音，拖慢回答",
        "",
    ]

    for item in results:
        lines.append("-" * 60)
        lines.append(f"Top-K = {item.top_k} | 实际命中 = {item.hit_count}")
        lines.append("-" * 60)

        if not item.previews:
            lines.append("（无命中结果）")
        else:
            for index, preview in enumerate(item.previews, start=1):
                lines.append(f"[{index}] {preview}")

        lines.append("")

    lines.append("=" * 60)
    lines.append("经验参考（可后续按你的文档调整）:")
    lines.append("- 简单事实题: Top-K = 2 ~ 4")
    lines.append("- 架构/流程题: Top-K = 4 ~ 6")
    lines.append("- 复杂对比题: Top-K = 6 ~ 8")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python eval_test.py <问题> [领域标签]")
        print("")
        print("示例:")
        print('  python eval_test.py "项目用了哪些技术栈" 后端')
        print('  python eval_test.py "RAG 的数据流是什么" 后端')
        sys.exit(1)

    user_question = sys.argv[1]
    user_domain = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        report = evaluate_top_k(user_question, domain=user_domain)
        print(format_eval_report(user_question, report, domain=user_domain))
    except Exception as exc:
        print(f"错误: {exc}")
        sys.exit(1)
