# -*- coding: utf-8 -*-
"""补齐 v1.0.0 与 v1.1.0 的版本存档 HTML。

背景：这两个 tag 只有 commit 指针，没有 archives/ 下的版本快照，
      导致 verify 报「有存档HTML = 否」——tag 无法直接比对文件内容。

做法：从各自 tag 指向的 commit 里取当时的 online/index.html，
      落到 archives/shooting-plan-workbench-<ver>.html。
      这是历史文件的原样搬运，不做任何改写。
"""
import base64
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_release import api, tag_sha  # noqa: E402

TARGET = {
    "v1.0.0": "在线版首发快照（release: v1.0.0 首个里程碑版本）",
    "v1.1.0": "存储加固版快照（release: v1.1.0 图片压缩 + 容量指示 + 触顶告警）",
}


def main():
    print("=== 补齐 v1.0.0 / v1.1.0 版本存档 ===")
    for ver, note in TARGET.items():
        dest = "archives/shooting-plan-workbench-%s.html" % ver
        if api("GET", "/contents/" + dest, allow_404=True) is not None:
            print("· %s 已有存档，跳过" % ver)
            continue

        # tag 指向 commit；取该 commit 里的在线版 HTML
        ref = api("GET", "/git/ref/tags/" + ver)
        if ref["object"]["type"] == "tag":
            commit_sha = api("GET", "/git/tags/" + ref["object"]["sha"])["object"]["sha"]
        else:
            commit_sha = ref["object"]["sha"]
        print("%s -> commit %s" % (ver, commit_sha[:8]))

        d = api("GET", "/contents/online/index.html?ref=" + commit_sha, allow_404=True)
        if d is None:
            d = api("GET", "/contents/workbench.html?ref=" + commit_sha, allow_404=True)
        if d is None:
            print("✗ %s 的 commit 里找不到 HTML，跳过" % ver)
            continue

        html = base64.b64decode(d["content"]).decode("utf-8")
        msg = "chore(%s): 补录版本存档快照\n\n%s\n\n来源：该 tag 指向 commit 的 online/index.html，原样搬运。" % (ver, note)
        from git_release import put_file
        put_file(dest, html, msg)
        print("   快照 %d KB\n" % (len(html.encode("utf-8")) // 1024))


if __name__ == "__main__":
    main()