# -*- coding: utf-8 -*-
"""补录历史版本快照与 tag（v1.0.7 ~ v1.0.10）。

背景：这4 个版本线上已发布、HTML 存档齐全，但都没打 tag，
导致「tag 停在 v1.1.0、线上已到 v1.0.11」——tag 无法用于版本比对。

做法：把每版HTML 推到 archives/ 作为不可变快照，再按时间顺序打 annotated tag。
      tag 指向「该版本快照入库后的 commit」，于是 git diff v1.0.9 v1.0.10
      能真实反映两版差异。

注意：v1.0.7 / v1.0.8 生成于版本徽章特性之前，文件内没有 APP_VER 常量，
      版本号只能靠文件名承载 —— 这是历史事实，不做回填改写。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_release import (  # noqa: E402
    BRANCH, api, head_sha, create_tag, put_file, tag_exists,
)

OUTPUTS = r"I:\ObsidianCatalogue\Workbuddy\WorkBuddy\2026-10-04-16-43-03\outputs"

#按时间先后排列（v1.0.7 是本地线最早的一版）
HISTORY = [
    ("v1.0.7",  "拍摄策划工作台-v1.0.7.html",
     "v1.0.7 — 本地文件线起点（原 v1.7）：章节重排+ 6.5 器材总表只读聚合 + 时段轴联动。\n\n"
     "版本号由 v1.7 重排为 v1.0.7（见 CHANGELOG v1.0.10 段「两条线并轨说明」）。\n"
     "本版生成于版本徽章特性之前，文件内无 APP_VER 常量，版本号由文件名承载。"),
    ("v1.0.8",  "拍摄策划工作台-v1.0.8.html",
     "v1.0.8 — 原 v1.8：时段轴与甘特图细节修正。\n\n"
     "版本号由 v1.8 重排为 v1.0.8。同样生成于版本徽章特性之前。"),
    ("v1.0.9",  "拍摄策划工作台-v1.0.9.html",
     "v1.0.9 — 章节重排定稿 + 6.5 器材总表实时聚合修复 + 版本徽章上线。\n\n"
     "本版起文件内含 APP_VER 常量，版本号不再靠文件名承载。\n"
     "6.5 不刷新的根因：patchLive() 缺「6.1–6.4 变化 → 重算 6.5」的触发链。"),
    ("v1.0.10", "拍摄策划工作台-v1.0.10.html",
     "v1.0.10 — §0.7 删除与 §1.1 重复的模特姓名输入框，摘要卡占满整行。\n\n"
     "同步机制由双向改单向：模特资料唯一可编辑处是 §1.1，§0.7 纯只读回显。\n"
     "同时确立版本号规则：本地线统一用 1.0.x 续写。"),
]


def main():
    print("=== 补录历史版本快照与 tag===")
    for ver, fname, note in HISTORY:
        src = os.path.join(OUTPUTS, fname)
        if not os.path.exists(src):
            print("✗ 缺文件 %s，跳过 %s" % (fname, ver))
            continue

        if tag_exists(ver):
            print("· tag %s 已存在，跳过" % ver)
            continue

        with io.open(src, encoding="utf-8", newline="") as f:
            html = f.read()

        msg = "chore(%s): 补录版本存档快照\n\n%s" % (ver, note)
        put_file("archives/shooting-plan-workbench-%s.html" % ver, html, msg)
        sha = head_sha()
        create_tag(ver, "拍摄策划工作台 %s\n\n%s" % (ver, note), sha)
        print("   快照 %d KB\n" % (len(html.encode("utf-8")) // 1024))

    print("=== 完成，校验三件套 ===")


if __name__ == "__main__":
    main()