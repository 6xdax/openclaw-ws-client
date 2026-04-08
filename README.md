# OpenClaw WebSocket Client

Python 连接 OpenClaw Gateway 的示例客户端。

## 环境管理（uv）

```bash
cd openclaw_ws_client

# 创建虚拟环境
uv sync

# 运行
uv run python client.py

# 安装依赖
uv add websockets
```

## 直接运行

```bash
uv run -- python client.py
```

## 功能

- ✅ Challenge-Response 握手认证
- ✅ 连接网关并获取 device token
- ✅ 订阅 session 变更事件
- ✅ 订阅指定 session 的消息
- ✅ 向 session 发送消息
- ✅ 列出所有 session
- ✅ 监听所有网关事件

## 配置

编辑 `config.py` 中的以下字段：

| 字段 | 说明 |
|------|------|
| `GATEWAY_URL` | Gateway 地址，默认 `ws://127.0.0.1:18789` |
| `TOKEN` | 你的 gateway token |
| `DEVICE_ID` | 设备 ID，每个客户端实例应唯一 |
