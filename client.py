"""OpenClaw Gateway WebSocket 客户端"""

import asyncio
import json
import base64
import random
import string
from websockets.asyncio import client
from cryptography.hazmat.primitives import serialization

from config import GATEWAY_URL, TOKEN, LOCALE, CLIENT_ID, CLIENT_VERSION, PLATFORM
from crypto_utils import (
    load_openclaw_identity,
    sign_device_auth_v2,
)

# Paired device info for the cli device
PAIR_DEVICE_ID = "0f1bdcc5264130913d2b683af66075fb63ae7d00334db24a3d11cbbe13c708cd"
PAIR_CLIENT_ID = "cli"
PAIR_CLIENT_MODE = "probe"
PAIR_ROLE = "operator"
PAIR_SCOPES = ["operator.read"]


def gen_nonce(length=32):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def build_connect_request(nonce: str, ts: int, token: str, private_key, public_key) -> dict:
    """构建已签名的 connect 请求"""
    payload = {
        "type": "req",
        "id": gen_nonce(),
        "method": "connect",
        "params": {
            "minProtocol": 3,
            "maxProtocol": 3,
            "client": {
                "id": PAIR_CLIENT_ID,
                "version": CLIENT_VERSION,
                "platform": PLATFORM,
                "mode": PAIR_CLIENT_MODE,
            },
            "role": PAIR_ROLE,
            "scopes": PAIR_SCOPES,
            "caps": [],
            "commands": [],
            "permissions": {},
            "auth": {"token": token},
            "locale": LOCALE,
            "userAgent": f"{CLIENT_ID}/{CLIENT_VERSION}",
        },
    }

    # 用 Ed25519 私钥签名 v2 设备认证 payload
    sig = sign_device_auth_v2(
        device_id=PAIR_DEVICE_ID,
        client_id=PAIR_CLIENT_ID,
        client_mode=PAIR_CLIENT_MODE,
        role=PAIR_ROLE,
        scopes=PAIR_SCOPES,
        signed_at_ms=ts,
        token=token,
        nonce=nonce,
        private_key=private_key,
    )

    # publicKey = raw 32-byte Ed25519 public key, base64 encoded
    raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_key_b64 = base64.b64encode(raw_bytes).decode()

    payload["params"]["device"] = {
        "id": PAIR_DEVICE_ID,
        "publicKey": public_key_b64,
        "signature": sig,
        "signedAt": ts,
        "nonce": nonce,
    }
    return payload


class OpenClawClient:
    def __init__(self, url=GATEWAY_URL):
        self.url = url
        self.ws = None
        self.device_token = None
        self.private_key, self.public_key, self.device_id = load_openclaw_identity()

    async def connect(self) -> bool:
        """完成 challenge-response 握手并连接网关"""
        self.ws = await client.connect(
            self.url,
            additional_headers={"Origin": "http://127.0.0.1:18789"},
        )
        print(f"[{self.url}] 已建立连接，等待 challenge...")

        # 1. 接收 challenge
        challenge = await self.ws.recv()
        ch_data = json.loads(challenge)
        nonce = ch_data["payload"]["nonce"]
        ts = ch_data["payload"]["ts"]
        print(f"[握手] 收到 challenge, nonce={nonce}")

        # 2. 构建并签名 connect 请求
        payload = build_connect_request(
            nonce, ts, TOKEN, self.private_key, self.public_key
        )

        # 3. 发送 connect
        await self.ws.send(json.dumps(payload, separators=(",", ":")))
        print("[握手] 已发送 connect 请求")

        # 4. 接收响应
        resp = await self.ws.recv()
        resp_data = json.loads(resp)

        if not resp_data.get("ok", False):
            print(f"[握手] 连接失败: {resp_data}")
            return False

        payload_type = resp_data.get("payload", {}).get("type")
        print(f"[握手] 收到响应: {payload_type}")

        if payload_type == "hello-ok":
            self.device_token = resp_data.get("payload", {}).get("auth", {}).get("deviceToken")
            print(f"[握手] ✅ 连接成功! deviceToken={self.device_token[:20]}...")
            return True

        print(f"[握手] ❌ 未知响应类型: {payload_type}")
        return False

    async def subscribe_sessions(self):
        """订阅 session 变更事件"""
        req = {
            "type": "req",
            "id": gen_nonce(),
            "method": "sessions.subscribe",
            "params": {},
        }
        await self.ws.send(json.dumps(req, separators=(",", ":")))
        print("[订阅] 已发送 sessions.subscribe")

    async def list_sessions(self):
        """列出所有 session"""
        req = {
            "type": "req",
            "id": gen_nonce(),
            "method": "sessions.list",
            "params": {},
        }
        await self.ws.send(json.dumps(req, separators=(",", ":")))
        resp = await self.ws.recv()
        return json.loads(resp)

    async def send_message(self, session_key: str, text: str):
        """向指定 session 发送消息"""
        req = {
            "type": "req",
            "id": gen_nonce(),
            "method": "chat.send",
            "params": {"sessionKey": session_key, "text": text},
        }
        await self.ws.send(json.dumps(req, separators=(",", ":")))
        print(f"[发送] session={session_key}, text={text}")

    async def listen(self):
        """监听并打印所有收到的消息"""
        async for msg in self.ws:
            data = json.loads(msg)
            t = data.get("type") or data.get("event", "")
            print(f"[消息] type={t}")
            if t == "event":
                print(f"         event={data.get('event')}")
                print(f"         payload={json.dumps(data.get('payload', {}), ensure_ascii=False)[:200]}")
            elif t == "res":
                print(f"         id={data.get('id')}, ok={data.get('ok')}")

    async def close(self):
        if self.ws:
            await self.ws.close()
            print("[关闭] 连接已关闭")


async def main():
    client_obj = OpenClawClient()
    ok = await client_obj.connect()
    if not ok:
        print("连接失败，退出")
        return

    await client_obj.subscribe_sessions()

    sessions_resp = await client_obj.list_sessions()
    print(f"[Session列表] {json.dumps(sessions_resp, ensure_ascii=False)[:500]}")

    print("\n开始监听消息（Ctrl+C 退出）...\n")
    await client_obj.listen()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n收到中断信号，退出")
