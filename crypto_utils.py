"""设备身份工具 - 从 OpenClaw 官方身份文件加载"""

import base64
import json
import os
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

IDENTITY_FILE = os.path.expanduser("~/.openclaw/identity/device.json")


def load_openclaw_identity():
    """从 OpenClaw 官方身份文件加载设备密钥对"""
    with open(IDENTITY_FILE) as f:
        data = json.load(f)

    device_id = data["deviceId"]
    private_key = serialization.load_pem_private_key(
        data["privateKeyPem"].encode(),
        password=None
    )
    public_key = private_key.public_key()
    return private_key, public_key, device_id


def sign_payload(nonce: str, payload_json: str, private_key) -> str:
    """用 Ed25519 私钥签名 v2 格式: nonce + payload_json"""
    msg = (nonce + payload_json).encode()
    sig = private_key.sign(msg)
    return base64.b64encode(sig).decode()


def build_device_auth_v2_payload(
    device_id: str,
    client_id: str,
    client_mode: str,
    role: str,
    scopes: list,
    signed_at_ms: int,
    token: str,
    nonce: str
) -> str:
    """
    构建设备认证 v2 payload（与 OpenClaw gateway 服务器端完全一致）

    格式: v2|{deviceId}|{clientId}|{clientMode}|{role}|{scopes}|{signedAtMs}|{token}|{nonce}
    """
    scopes_str = ",".join(scopes)
    parts = [
        "v2",
        device_id,
        client_id,
        client_mode,
        role,
        scopes_str,
        str(signed_at_ms),
        token or "",
        nonce
    ]
    return "|".join(parts)


def sign_device_auth_v2(
    device_id: str,
    client_id: str,
    client_mode: str,
    role: str,
    scopes: list,
    signed_at_ms: int,
    token: str,
    nonce: str,
    private_key
) -> str:
    """
    对设备认证 v2 payload 进行签名（使用 OpenClaw 的 plain Ed25519）
    返回 base64url 编码的签名
    """
    payload = build_device_auth_v2_payload(
        device_id, client_id, client_mode, role, scopes,
        signed_at_ms, token, nonce
    )
    sig = private_key.sign(payload.encode("utf-8"))
    # base64url encoding (no padding)
    sig_b64url = (
        base64.b64encode(sig)
        .replace(b"+", b"-")
        .replace(b"/", b"_")
        .rstrip(b"=")
        .decode()
    )
    return sig_b64url


if __name__ == "__main__":
    priv, pub, did = load_openclaw_identity()
    print(f"device_id: {did}")
    raw_pub = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    print(f"publicKey (raw base64): {base64.b64encode(raw_pub).decode()}")
