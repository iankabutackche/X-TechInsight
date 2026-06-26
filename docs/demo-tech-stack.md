# X-TechInsight 技术栈与架构说明（录屏演示专用）

> 本文档用于 **录屏演示上传**。上传时请将对话 **领域标签设为「后端」**。  
> 文件路径：`docs/demo-tech-stack.md`

---

## 一、项目简介

X-TechInsight 是一个 **模块化全栈 RAG 技术文档分析平台**。

用户可上传 PDF、Markdown、纯文本；系统对文档切分、向量化后存入 ChromaDB；提问时检索相关片段，再交给大模型生成回答，并标注 `[Source N]` 来源。

---

## 二、技术栈（录屏必问）

### 2.1 前端

- **React**：三栏 UI（对话列表 / 聊天区 / 配置面板）
- **Vite**：本地开发与生产构建
- **MessageMarkdown**：助手回复 Markdown 渲染与代码高亮

### 2.2 后端

- **FastAPI**：REST API + SSE 流式问答
- **SQLite**：存储对话（chats）与消息（messages）
- **SQLAlchemy**：ORM 数据访问
- **Uvicorn**：ASGI 服务器

### 2.3 AI 与 RAG

- **LangChain**：文档加载、切分、LLM 调用
- **OpenAI Embeddings**：文本向量化
- **gpt-4o-mini**：默认生成模型（temperature=0）
- **ChromaDB**：本地向量库，持久化目录 `backend/data/chroma`

### 2.4 部署

- **Render Static Site**：前端 `https://x-techinsight-web.onrender.com`
- **Render Web Service**：后端 `https://x-techinsight.onrender.com`

---

## 三、后端核心模块

| 文件 | 职责 |
|------|------|
| `loader.py` | 加载 PDF/MD/TXT，切分文本，注入 metadata |
| `vector_manager.py` | ChromaDB 入库与 Top-K 相似度检索 |
| `agent_logic.py` | RAG 问答、拒答策略、来源引用 |
| `database.py` | SQLite 表结构与 CRUD |
| `main.py` | FastAPI 路由、CORS、BackgroundTasks、SSE |

---

## 四、核心 API 接口

| 接口 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `POST /chats/create` | 创建对话（name + tag） |
| `GET /chats/list` | 对话列表 |
| `GET /chats/{id}/messages` | 对话历史 |
| `PATCH /chats/{id}` | 更新对话名称或 tag |
| `POST /files/upload` | 上传文档，后台异步入库 |
| `POST /query/stream` | SSE 流式问答 |

---

## 五、RAG 问答流程

1. 用户上传文档 → `loader` 切分 → OpenAI Embedding → 写入 ChromaDB  
2. 用户提问 → 按对话 **领域 tag** 过滤 → 检索 **Top-K=4** 相关片段  
3. 片段拼入 Prompt → gpt-4o-mini 流式生成 → 返回 `[Source N]` 引用  
4. 若检索不到相关片段 → 回答：**「根据现有资料，我无法回答这个问题。」**

---

## 六、关键默认参数

| 参数 | 默认值 |
|------|--------|
| Top-K | 4 |
| chunk_size | 1000 字符 |
| chunk_overlap | 150 字符 |
| 单文件大小上限 | 10MB |
| 支持格式 | `.pdf`、`.md`、`.txt` |

---

## 七、领域标签（domain）说明

- 每个对话有一个 tag，例如 **「后端」**、**「金融」**
- 上传文档时，文档片段 metadata 的 `domain` 字段 = 当前对话 tag
- 检索时使用 `filter={"domain": chat.tag}`，避免跨领域串答

---

## 八、录屏演示建议问题

### 应该能答（文档里有）

| 问题 | 期望要点 |
|------|----------|
| 项目用了哪些技术栈？ | React、Vite、FastAPI、SQLite、ChromaDB、LangChain、OpenAI |
| 向量库用的什么？ | ChromaDB |
| 默认 Top-K 是多少？ | 4 |
| 有哪些 API？ | /health、/chats/*、/files/upload、/query/stream |
| 资料不足时会怎样？ | 明确拒答，不编造 |

### 应该拒答（文档里没有）

| 问题 | 期望回答 |
|------|----------|
| 明天北京天气怎么样？ | 根据现有资料，我无法回答这个问题。 |
| 今天股市涨了多少？ | 根据现有资料，我无法回答这个问题。 |

---

## 九、注意事项

- OpenAI API Key 配置在 `backend/.env`，**禁止提交 Git**
- 扫描版 PDF、加密 PDF 暂不支持
- Render 免费版可能休眠，演示前请先访问 `/health` 唤醒后端

---

*上传本文件后，等待 10～30 秒解析完成，再在右侧勾选挂载，然后提问。*
