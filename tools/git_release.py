# -*- coding: utf-8 -*-
"""拍摄策划工作台 — 版本治理工具（对齐过往一般性任务标准）。

标准来源：VoiceDesk 仓库（voicedesk-repo）的 CONTRIBUTING.md
  · Conventional Commits（中文 subject、body 写为什么）
  · 语义化版本 + annotated tag
  · CHANGELOG 与 tag 严格对应
  · .gitignore 锚定根目录，禁止裸 `_*`

## 为什么必须走 REST API 而不是 git push

本机沙箱内 git 协议层被网络阻断（实测）：
  · git走代理 → CONNECT tunnel failed, 502
  · git 直连 →Failed to connect to github.com:443
  · 但 curl 走同一代理返回 200，REST API 也完全可用

结论：git fetch/push/tag 均不可用，所有远端写操作走 REST API。
这也是仓库里 `push_github.py` 当初被写出来的原因。

## 模块一：git_release.py —— 版本快照 + tag 治理

用法：
    python git_release.py plan-v1.0.11# 规划：看当前工作区状态
    python git_release.py tag v1.0.11 "发布说明"     # 推快照 + 打 tag
    python git_release.py tag-list                    # 列出全部 tag 与快照文件
    python git_release.py verify                     # 校验 tag 可比对性

约束：
  · 所有 tag 都是 annotated（带说明），lightweight tag 不带说明、不可追溯
  · 每个 tag 必须同时具备三样：git tag / CHANGELOG 段 / 版本存档 HTML
  · tag 一旦打出不删除、不移动（移动 tag 等于篡改历史）
"""
import base64
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

PY = r"C:\Users\Jason's Destop\.workbuddy\binaries\python\versions\3.13.12\python.exe"
TOKENSCRIPT = r"C:\Users\Jason's Destop\.workbuddy\skills\github-desktop-token\references\read_token.py"
REPO = "JasonWithMiracle/shooting-plan-workbench"
BRANCH = "main"
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_HTML = os.path.join(ROOT, "src", "online.html")
ARCHIVE_DIR = os.path.join(ROOT, "archives")
ASSET_DIR = os.path.join(ROOT, "assets")

TOKEN = subprocess.run([PY, TOKENSCRIPT], capture_output=True, text=True).stdout.strip()
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


# ---------------------------------------------------------------- GitHub API

def api(method, path, body=None, allow_404=False):
    url = "https://api.github.com/repos/%s%s" % (REPO, path)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "token " + TOKEN,
        "User-Agent": "workbuddy-release",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    try:
        raw = OPENER.open(req, timeout=60).read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        # 404 有两种含义：文件不存在（可容忍，走新建）vs 无权限（必须中止）。
        # 二者HTTP 码相同，只能靠路径语义区分 —— 文件类路径一律容忍。
        if e.code == 404 and allow_404 and _looks_like_file_path(path):
            return None
        raise SystemExit("GitHub API %s %s 失败 HTTP %s\n%s" % (method, path, e.code, detail))
    # DELETE 返回 204 No Content，body 为空 —— 不能无脑 json.loads，
    # 否则「操作其实成功了」会被误报成 JSON 解析崩溃（本项目真踩过）。
    if not raw:
        return {}
    return json.loads(raw)


def _looks_like_file_path(path):
    """判断 404 是否可容忍。

    GitHub 对「资源不存在」与「无权限」都返404，只能靠路径语义区分：
    · contents/ 下的条目 —— 文件可能不存在，走新建，必须容忍
    · git/ref/tags/<tag> —— tag 可能不存在（首次创建前），必须容忍
    · 其余（仓库、分支等）—— 404 意味着配置错误，必须中止
    """
    p = path.split("?")[0]
    return p.startswith("/contents/") or p.startswith("/git/ref/tags/")


def blob_sha(path, ref=BRANCH):
    """取远端文件 blob sha；不存在返回 None。"""
    d = api("GET", "/contents/" + path + "?ref=" + ref, allow_404=True)
    return d.get("sha") if d else None


def put_file(path, content, message):
    """写文件，带 sha 并发保护：远端被改过则 409，不静默覆盖。"""
    b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    sha = blob_sha(path)
    body = {"message": message, "content": b64, "branch": BRANCH}
    if sha:
        body["sha"] = sha
    else:
        print("· %-46s 远端不存在，转新建" % path)
    r = api("PUT", "/contents/" + path, body)
    c = r.get("content") or {}
    print("✓ %-46s %s" % (path, c.get("html_url", "")))
    return r.get("commit", {}).get("sha")


def put_blob_url(path, local_path, message):
    """用 Git Data API 传二进制（PDF/PNG 不适合 base64 进 contents API 的体积限制）。"""
    data = io.open(local_path, "rb").read()
    blob = api("POST", "/git/blobs", {"content": base64.b64encode(data).decode("ascii"),
                                      "encoding": "base64"})
    ref = api("GET", "/git/ref/heads/" + BRANCH)
    parent = ref["object"]["sha"]
    tree = api("POST", "/git/trees", {"base_tree": ref["object"]["sha"],
                                       "tree": [{"path": path, "mode": "100644",
                                                 "type": "blob", "sha": blob["sha"]}]})
    commit = api("POST", "/git/commits", {"message": message, "tree": tree["sha"],
                                          "parents": [parent]})
    api("PATCH", "/git/refs/heads/" + BRANCH, {"sha": commit["sha"]})
    print("✓ %-46s 二进制入库 %d KB" % (path, len(data) // 1024))
    return commit["sha"]


def create_tag(name, message, target_sha):
    """建 annotated tag。contents API 不能建 tag，必须走 git/tags + git/refs。"""
    if tag_exists(name):
        print("✗ tag %s 已存在，按标准不予移动（如确需更正，另开 hotfix tag）" % name)
        return None
    tag_obj = api("POST", "/git/tags", {
        "tag": name, "message": message, "object": target_sha,
        "type": "commit", "tagger": {"name": "JasonWithMiracle", "email": "122904020+JasonWithMiracle@users.noreply.github.com",
                                      "date": _now_iso()},
    })
    api("POST", "/git/refs", {"ref": "refs/tags/" + name, "sha": tag_obj["sha"]})
    print("✓ tag %-20s -> %s" % (name, target_sha[:8]))
    return tag_obj["sha"]


def _now_iso():
    import datetime
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def head_sha():
    return api("GET", "/git/ref/heads/" + BRANCH)["object"]["sha"]


def tag_exists(name):
    return api("GET", "/git/ref/tags/" + name, allow_404=True) is not None


def tag_sha(name):
    r = api("GET", "/git/ref/tags/" + name, allow_404=True)
    return r["object"]["sha"] if r else None


# ---------------------------------------------------------------- 版本号校验

def validate_ver(ver):
    """语义化版本校验。已知历史遗留：1.0.10 数字小于 1.1.0 但时间更晚，
    这是编号重排的结果，不是错误 —— 故只校验格式，不校验单调性。"""
    if not re.match(r"^v\d+\.\d+\.\d+$", ver):
        raise SystemExit("版本号格式非法：%s（应形如 v1.0.12）" % ver)
    major, minor, patch = (int(x) for x in ver[1:].split("."))
    if major == 0 and minor == 0 and patch == 0:
        raise SystemExit("版本号不能全为 0")
    return ver


# ---------------------------------------------------------------- 子命令

def cmd_plan(ver):
    validate_ver(ver)
    print("=== 发布前检查：%s ===" % ver)
    problems = []

    if not os.path.exists(SRC_HTML):
        print("✗ 缺少 src/online.html")
        problems.append("源文件缺失")
    else:
        size = os.path.getsize(SRC_HTML) // 1024
        with io.open(SRC_HTML, encoding="utf-8") as f:
            head = f.read()
        # 必须扫全文：文件开头还有若干处 APP_VER 引用（版本徽章渲染），
        # 唯独「常量声明」那行在文件中部偏后，只读开头会误判为「找不到」。
        m = re.search(r"APP_VER\s*=\s*'([^']+)'", head)
        if not m:
            problems.append("src/online.html 里找不到 APP_VER 常量")
            print("✗ 找不到 APP_VER（版本号单一事实源）")
        elif m.group(1) != ver:
            problems.append("APP_VER(%s) 与目标版本(%s) 不一致" % (m.group(1), ver))
            print("✗ APP_VER = %s，但准备发布 %s" % (m.group(1), ver))
        else:
            print("✓ APP_VER = %s，大小 %d KB" % (ver, size))

    try:
        if tag_exists(ver):
            problems.append("tag %s 已存在" % ver)
            print("✗ tag %s 已存在" % ver)
        else:
            print("✓ tag %s 尚未占用" % ver)
    except SystemExit as e:
        problems.append("tag 查询失败：%s" % e)
        print("✗ tag 查询失败")

    changelog = api("GET", "/contents/CHANGELOG.md?ref=" + BRANCH, allow_404=True)
    changelog = base64.b64decode(changelog["content"]).decode("utf-8") if changelog else ""
    if re.search(r"^## \[%s\]" % re.escape(ver), changelog, re.M):
        print("✓ CHANGELOG 已有 %s 段" % ver)
    else:
        problems.append("CHANGELOG.md 缺 %s 段" % ver)
        print("✗ CHANGELOG.md 缺 %s 段" % ver)

    print()
    if problems:
        print("发现 %d 个问题，未满足发布标准：" % len(problems))
        for p in problems:
            print("  ·", p)
        raise SystemExit(1)
    print("全部检查通过，可以执行 tag 发布。")


def cmd_tag(ver, message):
    """版本发布：推代码快照 + 版本存档 + 打 annotated tag。"""
    validate_ver(ver)
    if not os.path.exists(SRC_HTML):
        raise SystemExit("缺少 src/online.html")
    with io.open(SRC_HTML, encoding="utf-8") as f:
        html = f.read()

    m = re.search(r"APP_VER\s*=\s*'([^']+)'", html)
    if not m or m.group(1) != ver:
        raise SystemExit("src/online.html 的 APP_VER 与目标版本不符，终止")

    msg = message or ("release: %s\n\n版本快照与 tag 同步入库。" % ver)

    print("=== 发布 %s ===" % ver)
    # 0. CHANGELOG 先行：检查器校验的是远端 CHANGELOG，本地改完必须先推
    local_cl = os.path.join(ROOT, "CHANGELOG.md")
    if os.path.exists(local_cl):
        with io.open(local_cl, encoding="utf-8") as f:
            cl = f.read()
        d = api("GET", "/contents/CHANGELOG.md?ref=" + BRANCH, allow_404=True)
        remote_cl = base64.b64decode(d["content"]).decode("utf-8") if d else ""
        if cl != remote_cl:
            put_file("CHANGELOG.md", cl, "docs(%s): 补记 CHANGELOG 版本段" % ver)
        else:
            print("· CHANGELOG.md 无变化，跳过")

    # 1. 在线版与离线版两处保持同源
    put_file("online/index.html", html, msg)
    put_file("src/online.html", html, msg)
    # 2. 版本存档（tag 的比对依据）
    put_file("archives/shooting-plan-workbench-%s.html" % ver, html, msg)
    # 3. 打 tag 指向当前 HEAD
    sha = head_sha()
    create_tag(ver, "拍摄策划工作台 %s\n\nAPP_VER 单一事实源：%s" % (ver, ver), sha)
    print("\n完成。比对方式：git diff v1.0.10 %s" % ver)


def cmd_tag_list():
    tags = api("GET", "/tags?per_page=100")
    print("=== 远端 tag 清单（共 %d 个）===" % len(tags))
    print("%-12s %-10s %s" % ("tag", "commit", "tag 说明"))
    for t in tags:
        sha = t["commit"]["sha"][:8]
        r = api("GET", "/git/ref/tags/" + t["name"], allow_404=True)
        if not r:
            msg = "(读取失败)"
        elif r["object"]["type"] == "tag":
            obj = api("GET", "/git/tags/" + r["object"]["sha"])
            msg = obj["message"].splitlines()[0][:48]
        else:
            msg = "(lightweight tag，无说明 —— 不符合标准)"
        print("%-12s %-10s %s" % (t["name"], sha, msg))


def cmd_verify():
    """校验三件套一致性：tag / 版本存档 / CHANGELOG 段。"""
    print("=== tag 可比对性校验 ===")
    tags = [t["name"] for t in api("GET", "/tags?per_page=100")]
    d = api("GET", "/contents/CHANGELOG.md?ref=" + BRANCH, allow_404=True)
    changelog = base64.b64decode(d["content"]).decode("utf-8") if d else ""

    print("%-12s %-14s %-14s %s" % ("tag", "annotated", "有存档HTML", "CHANGELOG段"))
    ok_all = True
    for ver in tags:
        r = api("GET", "/git/ref/tags/" + ver, allow_404=True)
        if not r:
            annotated = "读取失败"
            ok_all = False
        elif r["object"]["type"] == "tag":
            annotated = "是"
        else:
            annotated = "否(lightweight)"
            ok_all = False
        if api("GET", "/contents/archives/shooting-plan-workbench-%s.html" % ver,
               allow_404=True) is not None:
            arch = "是"
        else:
            arch = "否"
            ok_all = False
        cl = "是" if re.search(r"^## \[%s\]" % re.escape(ver), changelog, re.M) else "否"
        if cl == "否":
            ok_all = False
        print("%-12s %-14s %-14s %s" % (ver, annotated, arch, cl))

    print()
    print("结论：", "全部通过，可用于版本比对" if ok_all else "存在缺口，见上表「否」项")


def cmd_diff(a, b):
    """比对两个版本的实际代码差异（tag 的核心用途）。

    每个 tag 的 commit 只含本版存档，且文件名带版本号（互不相同），
    所以 compare API 不会报 files —— 需要显式把两版存档取出来做内容 diff。
    """
    print("=== %s -> %s 差异 ===" % (a, b))
    ca = _tag_commit(a)
    cb = _tag_commit(b)
    ha = _archive_hash(a, ca)
    hb = _archive_hash(b, cb)
    print("  %-9s %s  sha256=%s" % (a, ca[:8], ha[1]))
    print("  %-9s %s  sha256=%s" % (b, cb[:8], hb[1]))
    if ha[1] == hb[1]:
        print("\n两版内容完全相同。")
        return
    import difflib
    la = base64.b64decode(ha[2]).decode("utf-8", "replace").splitlines()
    lb = base64.b64decode(hb[2]).decode("utf-8", "replace").splitlines()
    diff = list(difflib.unified_diff(la, lb, fromfile=a, tofile=b, n=1, lineterm=""))
    adds = sum(1 for x in diff if x.startswith("+") and not x.startswith("+++"))
    dels = sum(1 for x in diff if x.startswith("-") and not x.startswith("---"))
    print("\n共 +%d / -%d 行（%d → %d 行）\n" % (adds, dels, len(la), len(lb)))
    for line in diff[:60]:
        print("  " + line[:150])
    if len(diff) > 60:
        print("  ...（其余 %d 行略）" % (len(diff) - 60))


def _tag_commit(ver):
    ref = api("GET", "/git/ref/tags/" + ver)
    if ref["object"]["type"] == "tag":
        return api("GET", "/git/tags/" + ref["object"]["sha"])["object"]["sha"]
    return ref["object"]["sha"]


def _archive_hash(ver, commit):
    import hashlib
    d = api("GET", "/contents/archives/shooting-plan-workbench-%s.html?ref=%s" % (ver, commit),
            allow_404=True)
    if d is None:
        raise SystemExit("· %s 无版本存档，无法比对" % ver)
    raw = base64.b64decode(d["content"])
    return len(raw), hashlib.sha256(raw).hexdigest()[:12], d["content"]


def cmd_snapshot(msg):
    """只推代码快照，不打 tag（用于日常提交）。"""
    with io.open(SRC_HTML, encoding="utf-8") as f:
        html = f.read()
    print("=== 代码快照 ===")
    put_file("online/index.html", html, msg)
    put_file("src/online.html", html, msg)
    print("HEAD =", head_sha()[:8])


# ---------------------------------------------------------------- CLI

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("可用子命令：plan-v / tag / tag-list / verify / snapshot")
        return
    cmd = sys.argv[1]
    if cmd == "plan-v" and len(sys.argv) >= 3:
        cmd_plan(sys.argv[2])
    elif cmd == "tag" and len(sys.argv) >= 3:
        cmd_tag(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "tag-list":
        cmd_tag_list()
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "snapshot" and len(sys.argv) >= 3:
        cmd_snapshot(sys.argv[2])
    elif cmd == "diff" and len(sys.argv) >= 4:
        cmd_diff(sys.argv[2], sys.argv[3])
    else:
        print("参数错误。用法见文件头docstring。")
        raise SystemExit(2)


if __name__ == "__main__":
    main()