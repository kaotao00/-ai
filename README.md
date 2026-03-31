# AI管家私有化问答系统

这是一个面向企业内部知识管理与数据安全场景的私有化 AI 问答系统示例项目。

能力包括：

- 基于 `Ollama` 的本地模型调用
- 基于 `LangChain` 风格的 RAG 问答链路
- 基于 `Milvus` 的向量库接入预留
- 本地向量检索兜底，可直接运行
- 文档切分、向量化、入库、更新管理
- CLI、FastAPI、中文前端三种使用方式

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行命令行问答

```bash
python main.py ask --question "企业内部知识库问答系统如何保障数据安全？"
```

### 3. 导入文档

```bash
python main.py ingest --file data/sample_docs/security_policy.txt --category policy
```

### 4. 启动 API 服务

```bash
python start_server.py
```

打开 `http://127.0.0.1:8010/docs` 可查看接口。

### 5. 打开中文前端页面

```bash
http://127.0.0.1:8010
```

前端支持：

- 中文问答
- 仅检索知识
- 查看知识统计
- 上传企业文档入库
- 查看 Ollama 和 Milvus 诊断信息

## 可选配置

### 使用 Ollama

```bash
set AI_BUTLER_USE_OLLAMA=1
set AI_BUTLER_OLLAMA_MODEL=qwen2.5:7b
set AI_BUTLER_OLLAMA_BASE_URL=http://127.0.0.1:11434
```

建议先检查：

```bash
ollama list
ollama run qwen2.5:7b
```

### 使用 Milvus

```bash
set AI_BUTLER_USE_MILVUS=1
set AI_BUTLER_MILVUS_URI=http://localhost:19530
```

若 Ollama 或 Milvus 不可用，系统会自动回退到本地 mock 生成与本地向量检索，方便演示与开发。

## 真实接入说明

- 当 `AI_BUTLER_USE_OLLAMA=1` 时，系统会直接调用 `Ollama /api/generate`
- 当 `AI_BUTLER_USE_MILVUS=1` 时，系统会优先使用 Milvus 作为向量库
- `/health` 会返回当前模型、检索后端以及诊断信息，便于确认是否真正连上 Ollama 和 Milvus
