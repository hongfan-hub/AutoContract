# API Guard

面向前后端接口联调的多 Agent MVP，目标是把“文档落后于代码”“环境问题互相扯皮”“复现链路长”这三类问题压到最低。

## 核心能力

- `嗅探 Agent`：扫描目标代码仓库的最新提交，检测新增 Commit 和文件变更。
- `契约 Agent`：分析 Python/FastAPI 接口代码，逆向生成最新 OpenAPI 3.1 文档。
- `压测 Agent`：基于 OpenAPI 自动生成 Mock 数据和测试用例，对测试环境发起请求并留存请求/响应证据。
- `防扯皮证据链`：自动归档 commit、文件 diff、OpenAPI、测试结果、复现脚本、Markdown 报告。

## 项目结构

```text
src/api_guard/
  agents/                 三个 Agent
  analyzers/              代码静态分析
  generators/             用例和复现脚本生成
  openapi/                OpenAPI 文档生成
  publishers/             推送到 API 管理平台
  services/               git、状态、存证、HTTP 调用
  server.py               FastAPI API
  scheduler.py            定时轮询
examples/demo_backend/    示例 FastAPI 后端
scripts/                  启动脚本
config.example.toml       配置模板
```

## 工作流

1. 嗅探 Agent 读取仓库最新 `HEAD` 与上次记录的 commit。
2. 如果发现新 commit，则抓取 diff、文件列表和提交元信息。
3. 契约 Agent 扫描 Python/FastAPI 路由和 Pydantic 模型，生成 OpenAPI。
4. 文档可自动推送到 API 管理平台。
5. 压测 Agent 从 OpenAPI 生成测试用例和 Mock 数据，对测试环境执行闭环校验。
6. 所有证据统一落到 `artifacts/<repo>/<commit>/`。

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
pip install email-validator
```

### 2. 准备配置

```bash
copy config.example.toml config.toml
```

如果你在 Windows PowerShell：

```powershell
Copy-Item config.example.toml config.toml
```

默认配置已指向示例仓库 `examples/demo_backend` 和测试地址 `http://127.0.0.1:8001`。

### 3. 初始化示例仓库 git

```powershell
Set-Location .\examples\demo_backend
git init
git add .
git commit -m "init demo backend"
Set-Location ..\..
```

### 4. 启动示例后端

```powershell
.\scripts\run_demo_backend.ps1
```

### 5. 启动 API Guard

```powershell
Copy-Item config.example.toml config.toml
.\scripts\run_api_guard.ps1
```

服务默认运行在 `http://127.0.0.1:8099`。

## API

### 健康检查

```http
GET /healthz
```

### 查看配置

```http
GET /config
```

### 查看最近运行

```http
GET /dashboard
```

### 手动触发单仓库联调

```http
POST /runs
Content-Type: application/json

{
  "repo_name": "demo-backend",
  "force": true
}
```

### 手动触发全部仓库

```http
POST /runs/all?force=true
```

## 输出物

每次运行会在 `artifacts/<repo>/<commit>/` 下生成：

- `contract_bundle.json`：commit 元数据、diff、路由与契约详情。
- `openapi.json`：最新 OpenAPI 规范。
- `verification_report.json`：逐请求的请求头、请求体、响应码、响应体、耗时。
- `replay_requests.py`：一键复现的 Python 请求脚本。
- `report.md`：给研发、测试、产品、负责人看的摘要报告。

## 为什么它能“防扯皮”

- 文档不是手写，而是从代码和 commit 自动逆向。
- 测试不是口头描述，而是自动执行且留下请求/响应证据。
- 报错不是一句“你这边看看”，而是能定位到具体 commit、具体接口、具体 payload。
- 一旦环境、网关、鉴权、字段定义有偏差，都能在同一份报告里对齐。

## 当前 MVP 边界

- 当前静态分析优先支持 `Python + FastAPI + Pydantic`。
- 复杂泛型、依赖注入、动态路由和多层 `router.include_router()` 还没有完全覆盖。
- OpenAPI 推送目前通过通用 HTTP 请求实现，方便对接 Apifox、SwaggerHub、自研平台。
- 压测 Agent 目前是联调闭环验证，严格意义上的高并发压测可继续接入 Locust、k6 或 JMeter。

## 下一步可扩展

- 支持 Java/Spring、Node/NestJS、Go/Gin 的代码逆向。
- 接 LLM 做更强的语义契约推理与字段说明补全。
- 自动生成前端 Playwright/Cypress 联调脚本。
- 接入企业微信、飞书、Slack，自动推送失败报告。
- 接 CI/CD，在 PR 合并后自动跑全链路验证。
