# -*- coding: utf-8 -*-
"""探测 GitHub 通道可用性：git 协议层 vs REST API。

用途：确认沙箱内能否直接 git push，还是必须走 REST API。
每次执行前先跑这个，不要盲目试 git push。
"""
import json
import subprocess
import sys
import urllib.request

PY = r"C:\Users\Jason's Destop\.workbuddy\binaries\python\versions\3.13.12\python.exe"
TOKENSCRIPT = r"C:\Users\Jason's Destop\.workbuddy\skills\github-desktop-token\references\read_token.py"
REPO = "JasonWithMiracle/shooting-plan-workbench"

TOKEN = subprocess.run([PY, TOKENSCRIPT], capture_output=True, text=True).stdout.strip()
print("token 前缀:", TOKEN[:7])

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api(path):
    req = urllib.request.Request(
        "https://api.github.com/repos/%s%s" % (REPO, path),
        headers={
            "Authorization": "token " + TOKEN,
            "User-Agent": "workbuddy-probe",
            "Accept": "application/vnd.github+json",
        },
    )
    return json.loads(opener.open(req, timeout=30).read())


info = api("")
print("REST API: 可用 | default_branch =", info["default_branch"], "| size =", info["size"], "KB")

tags = api("/tags?per_page=100")
print("REST API 现有 tag:", [t["name"] for t in tags] or "无")

commits = api("/commits?perPage=1")
print("REST API 最近提交:", commits[0]["sha"][:8] if commits else "无")

print()
print("--- git 协议层 ---")
for label, args in (
    ("走代理", ["-c", "http.proxy=http://127.0.0.1:6421"]),
    ("直连", ["-c", "http.proxy=", "-c", "https.proxy="]),
):
    r = subprocess.run(
        ["git"] + args + ["ls-remote", "--heads", "gh"],
        capture_output=True, text=True, cwd=r"I:\ObsidianCatalogue\Workbuddy\WorkBuddy\2026-10-04-16-43-03\work",
    )
    ok = r.returncode == 0 and "main" in r.stdout
    print("%-6s git ls-remote: %s" % (label, "可用" if ok else "不可用"))
    if not ok:
        print("       ", (r.stderr or "").strip().splitlines()[0][:100] if r.stderr.strip() else "")