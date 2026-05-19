#!/usr/bin/env bash
# 检查远端部署机的 typeset-engine 仓库相对本地的 drift
#
# 用法:
#   bash deploy/native/check-drift.sh                    # 默认 host=sg2, path=/root/typeset-engine
#   bash deploy/native/check-drift.sh hk2                # 换 host
#   bash deploy/native/check-drift.sh sg2 /opt/typeset   # 换 path
#
# 输出:
#   - remote HEAD vs local HEAD (短 hash + subject)
#   - remote 落后的 commits (本地领先)
#   - remote 领先的 commits (理论=0, 除非 hot-fix)
#   - drift count + 推荐操作

set -euo pipefail

HOST="${1:-sg2}"
REMOTE_PATH="${2:-/root/typeset-engine}"
BRANCH="${BRANCH:-master}"   # 2026-05-19 起 master 成为 canonical, 原 deploy/native 已删

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# 颜色
red()    { printf '\033[1;31m%s\033[0m' "$*"; }
green()  { printf '\033[1;32m%s\033[0m' "$*"; }
yellow() { printf '\033[1;33m%s\033[0m' "$*"; }
cyan()   { printf '\033[1;36m%s\033[0m' "$*"; }

echo "=== typeset-engine drift check ==="
echo "  local repo : $REPO_ROOT"
echo "  branch     : $BRANCH"
echo "  remote host: $HOST"
echo "  remote path: $REMOTE_PATH"
echo

# 本地 HEAD
local_head=$(git rev-parse HEAD)
local_short=$(git rev-parse --short HEAD)
local_subject=$(git log -1 --pretty=%s HEAD)
local_branch=$(git rev-parse --abbrev-ref HEAD)

if [[ "$local_branch" != "$BRANCH" ]]; then
    yellow "[!] local branch is $local_branch, not $BRANCH"
    echo
fi

# 远端 HEAD (容错: ssh 失败 / 仓库不存在)
remote_info=$(ssh -o ConnectTimeout=10 -o BatchMode=yes "$HOST" \
    "cd '$REMOTE_PATH' 2>/dev/null && git rev-parse HEAD && git rev-parse --short HEAD && git log -1 --pretty=%s HEAD" 2>&1 || true)

if [[ -z "$remote_info" ]] || echo "$remote_info" | grep -qE "No such|not a git|Connection|Permission"; then
    red "[x] 无法访问 $HOST:$REMOTE_PATH"
    echo "$remote_info"
    exit 1
fi

remote_head=$(echo "$remote_info" | sed -n 1p)
remote_short=$(echo "$remote_info" | sed -n 2p)
remote_subject=$(echo "$remote_info" | sed -n 3p)

echo "local  HEAD: $(cyan "$local_short")  $local_subject"
echo "remote HEAD: $(cyan "$remote_short")  $remote_subject"
echo

if [[ "$local_head" == "$remote_head" ]]; then
    green "[+] in sync — no drift"
    exit 0
fi

# 用本地 git 算 ahead/behind (要求本地有 remote 的 commit, 通常 origin/$BRANCH fetch 后都有)
behind_count=0
ahead_count=0
if git cat-file -e "$remote_head" 2>/dev/null; then
    behind_count=$(git rev-list --count "$remote_head..$local_head" 2>/dev/null || echo 0)
    ahead_count=$(git rev-list --count "$local_head..$remote_head" 2>/dev/null || echo 0)
else
    yellow "[!] 本地没有 remote 的 commit $remote_short — 先 git fetch 再试"
    exit 2
fi

if [[ "$behind_count" -gt 0 ]]; then
    echo "$(yellow "remote 落后")本地 $behind_count commits:"
    git log --oneline --reverse "$remote_head..$local_head"
    echo
fi

if [[ "$ahead_count" -gt 0 ]]; then
    echo "$(red "remote 领先")本地 $ahead_count commits (远端有 hot-fix? 没拉回!):"
    git log --oneline --reverse "$local_head..$remote_head" 2>/dev/null || \
        echo "  (本地 git 没有这些 commit, 需要 git fetch)"
    echo
fi

echo "=== 推荐操作 ==="
if [[ "$behind_count" -gt 0 && "$ahead_count" -eq 0 ]]; then
    echo "在 $HOST 上执行:"
    echo "  cd $REMOTE_PATH && git pull origin $BRANCH && sudo -E bash deploy/native/install.sh"
elif [[ "$ahead_count" -gt 0 ]]; then
    echo "remote 有未拉回的 commit, 先在本地 git fetch + git log 看是什么再决定"
fi

exit 0
