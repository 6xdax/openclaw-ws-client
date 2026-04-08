# OpenClaw Python SDK

Python SDK for OpenClaw Gateway. Connect to your OpenClaw agent runtime via WebSocket.

## 安装

```bash
pip install openclaw-sdk
# 或从源码
git clone https://github.com/6xdax/openclaw-ws-client.git
cd openclaw-ws-client
uv sync
```

## 快速开始

```python
import asyncio
from openclaw import OpenClawClient

async def main():
    async with OpenClawClient() as client:
        # 列出所有 Agent
        agents = await client.agents.list()
        print(f"找到 {len(agents)} 个 Agent")

        # 创建 Session
        session = await client.sessions.create(
            agent_id=agents[0]["agentId"],
            title="我的对话"
        )
        print(f"创建 Session: {session['sessionKey']}")

        # 发送消息
        await client.sessions.send(session["sessionKey"], "你好！")

        # 获取消息预览
        messages = await client.sessions.preview(session["sessionKey"], limit=5)
        print(f"最近 {len(messages)} 条消息")

        # 删除 Session
        await client.sessions.delete(session["sessionKey"])

asyncio.run(main())
```

## 环境配置

SDK 会从环境变量读取配置（可选）：

```bash
# .env 文件
OPENCLAW_TOKEN=your_gateway_token
OPENCLAW_URL=ws://127.0.0.1:18789
OPENCLAW_DEVICE_ID=your_device_id  # 可选，自动从密钥推导
```

## API 概览

### OpenClawClient

```python
async with OpenClawClient() as client:
    await client.connect()   # 手动连接
    client.on("agent", handler)  # 注册事件处理器
    await client.close()
```

### Agents（智能体管理）

```python
# 列出所有 Agent
agents = await client.agents.list()

# 创建 Agent
agent = await client.agents.create(
    name="我的助手",
    model="minimax-m2.7",
    prompts={"system": "你是一个有帮助的助手"},
    skills=["weather", "calculator"]
)

# 更新 Agent
agent = await client.agents.update(agent_id, name="新名称")

# 删除 Agent
await client.agents.delete(agent_id)

# Agent 文件操作
files = await client.agents.files_list(agent_id)
content = await client.agents.files_get(agent_id, "prompts/system.txt")
await client.agents.files_set(agent_id, "prompts/system.txt", "新的系统提示")
```

### Sessions（对话会话管理）

```python
# 列出所有 Session
sessions = await client.sessions.list()

# 创建 Session
session = await client.sessions.create(
    agent_id="agent-xxx",
    title="新对话"
)

# 发送消息
await client.sessions.send(session["sessionKey"], "你好！")

# 订阅 Session 事件
await client.sessions.subscribe(session["sessionKey"])

# 订阅消息流
await client.sessions.messages_subscribe(session["sessionKey"])

# 中止执行
await client.sessions.abort(session["sessionKey"])

# 重置 Session（清空历史）
await client.sessions.reset(session["sessionKey"])

# 修改 Session
await client.sessions.patch(session["sessionKey"], title="新标题", pinned=True)

# 压缩 Session
await client.sessions.compact(session["sessionKey"])

# 获取消息预览
messages = await client.sessions.preview(session["sessionKey"], limit=10)

# 删除 Session
await client.sessions.delete(session["sessionKey"])
```

### Tools（工具管理）

```python
# 列出所有可用工具
tools = await client.tools.catalog()

# 列出生效的工具
active_tools = await client.tools.effective()

# 启用工具
await client.tools.enable("weather")

# 禁用工具
await client.tools.disable("weather")
```

## 事件监听

```python
async def on_agent_event(payload):
    print(f"Agent event: {payload}")

async def on_session_tool(payload):
    print(f"Tool call: {payload}")

client = OpenClawClient()
client.on("agent", on_agent_event)
client.on("session.tool", on_session_tool)

async with client:
    await client.sessions.subscribe()
    # keep running...
```

## 错误处理

```python
from openclaw import (
    OpenClawError,
    ConnectionError,
    AuthenticationError,
    AgentNotFoundError,
    SessionNotFoundError,
)

try:
    async with OpenClawClient() as client:
        await client.agents.delete("non-existent-id")
except AgentNotFoundError as e:
    print(f"Agent not found: {e}")
except OpenClawError as e:
    print(f"OpenClaw error: {e.message}, code: {e.code}")
```

## 项目结构

```
openclaw/
├── __init__.py       # SDK 入口
├── client.py         # OpenClawClient 核心类
├── agents.py         # Agent 管理
├── sessions.py       # Session 管理
├── tools.py          # Tools 管理
├── exceptions.py     # 异常定义
└── crypto_utils.py  # 加密签名工具
```

## 依赖

- Python >= 3.12
- websockets >= 12.0
- cryptography >= 46.0
- python-dotenv >= 1.0

## License

MIT
