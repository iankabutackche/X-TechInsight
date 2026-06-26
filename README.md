# X-TechInsight

模块化全栈 RAG 技术文档分析平台：支持多对话并存、动态知识库挂载、流式问答与引用溯源。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Vite |
| 后端 | FastAPI + SQLite |
| AI | LangChain + OpenAI |
| 向量库 | ChromaDB |

## 项目结构

```
X-TechInsight/
├── backend/          # Python 后端
│   ├── loader.py           # 文档加载与切分
│   ├── vector_manager.py   # 向量库管理
│   ├── agent_logic.py      # RAG 问答逻辑
│   ├── database.py         # SQLite 模型
│   ├── main.py             # FastAPI 入口
│   └── .env                # API Key（勿提交 Git）
└── frontend/         # React 前端
    └── src/
        ├── api.js          # API 封装
        ├── App.jsx           # 主界面
        └── MessageMarkdown.jsx
```

## 本地运行

### 1. 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart

# 配置 API Key
nano .env
# OPENAI_API_KEY=sk-你的Key

# 若需代理（国内访问 OpenAI）
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

python main.py
```

后端地址：http://127.0.0.1:8000  
API 文档：http://127.0.0.1:8000/docs

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：http://localhost:5173

## 核心 API

| 接口 | 说明 |
|------|------|
| `POST /chats/create` | 创建对话 |
| `GET /chats/list` | 对话列表 |
| `GET /chats/{id}/messages` | 对话历史 |
| `POST /files/upload` | 上传文档 |
| `POST /query/stream` | 流式问答（SSE） |

## 面试亮点（可写进简历）

1. **领域标签过滤**：ChromaDB 检索时用 `domain` 缩小向量搜索空间  
2. **对话空间隔离**：每个 ChatID 独立 SQLite 消息记录  
3. **RAG 溯源**：SSE 流式回答 + `[Source N]` 来源证据  
4. **异步上传**：FastAPI `BackgroundTasks` 非阻塞解析大文件  
5. **Markdown 渲染**：技术文档回答支持代码高亮

## Docker 部署（后端）

```bash
cd backend
docker build -t x-techinsight-api .
docker run -p 8000:8000 --env-file .env x-techinsight-api
```

## 注意事项

- 单文件建议 ≤ 10MB
- `.env` 禁止提交到 GitHub
- 扫描版 PDF 暂不支持
- 加密 PDF 会返回友好错误提示
