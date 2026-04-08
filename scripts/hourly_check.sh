#!/bin/bash
# 每小时检查项目状态脚本
# 使用方法: ./hourly_check.sh

PROJECT_DIR="/home/x/openclaw_project/openclaw_ws_client"
LOG_FILE="/tmp/openclaw_ws_client_check.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

echo "=== [$TIMESTAMP] 项目检查 ===" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit 1

# 1. 检查 git 状态
if [ -d ".git" ]; then
    if ! git diff --quiet 2>/dev/null; then
        echo "[!] 有未提交的更改" >> "$LOG_FILE"
        git diff --stat >> "$LOG_FILE"
    else
        echo "[OK] 无未提交更改" >> "$LOG_FILE"
    fi
fi

# 2. 检查依赖是否完整
if [ -f "pyproject.toml" ]; then
    echo "[OK] pyproject.toml 存在" >> "$LOG_FILE"
fi

# 3. 检查关键文件
for f in client.py crypto_utils.py config.py pyproject.toml; do
    if [ -f "$f" ]; then
        echo "[OK] $f 存在" >> "$LOG_FILE"
    else
        echo "[!] $f 缺失" >> "$LOG_FILE"
    fi
done

# 4. 检查客户端是否在运行
if pgrep -f "uv run python client.py" > /dev/null 2>&1; then
    echo "[OK] 客户端运行中" >> "$LOG_FILE"
else
    echo "[!] 客户端未运行" >> "$LOG_FILE"
fi

echo "---" >> "$LOG_FILE"
