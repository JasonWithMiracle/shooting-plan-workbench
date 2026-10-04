# -*- coding: utf-8 -*-
"""按正确时序重建 v1.0.7 ~ v1.0.11 的 tag（一次性建链 + 立即打 tag）。

## 为什么要重建

首次补录用「推一份存档 → 立刻在 HEAD 打 tag」，于是 tag 时序等于
「我操作的速度」而非版本先后：

    v1.0.11  01:01:46   ← 先打（开发得最完，最先补录）
    v1.0.7   01:03:14   ← 后打
    ...
    v1.0.10  01:03:32

结果 `git diff v1.0.10 v1.0.11` 返回 0 commits —— Git 认定 v1.0.11 是
v1.0.10 的祖先。tag 看得见却不能用来比对，等于没治理。

## 本脚本的要点

**建链与打 tag 必须交替进行，不能分两步。**
GitHub 会 GC 掉不被任何 ref 引用的对象 —— 上一版脚本先建链、最后才打 tag，
结果链上 5 个 commit 在打 tag 前就被回收（直读返回 404）。
tag 本身就是 ref，能锚定 commit，所以每建一个 commit 立刻给它打 tag。

**每个 commit 只含本版存档**，父链与时间戳严格递增，tag 天然有序。
main 上并行会话的工作内容由链尾的 merge commit 双父保住，零覆盖。
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_release import api  # noqa: E402

BRANCH = "main"
AUTHOR = {"name": "JasonWithMiracle",
          "email": "122904020+JasonWithMiracle@users.noreply.github.com"}
TZ = datetime.timezone(datetime.timedelta(hours=8))
T0 = datetime.datetime(2026, 10, 4, 17, 0, 0, tzinfo=TZ)


def stamp(minutes):
    return (T0 + datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S+08:00")


CHAIN = [
    ("v1.0.7", "archives/shooting-plan-workbench-v1.0.7.html",
     "章节重排（布光 6.5→7、行程 7→8）+ 6.5器材总表只读聚合 + 时段轴联动\n\n"
     "编号由原 v1.7 重排为 v1.0.7（见 CHANGELOG v1.0.10 段「两条线并轨说明」）。"),
    ("v1.0.8", "archives/shooting-plan-workbench-v1.0.8.html",
     "时段轴与甘特图细节修正（节点布局、时刻标注）\n\n编号由原 v1.8 重排为 v1.0.8。"),
    ("v1.0.9", "archives/shooting-plan-workbench-v1.0.9.html",
     "6.5 器材总表实时聚合修复 + 版本徽章上线（APP_VER 单一事实源）\n\n"
     "根因：patchLive() 缺「6.1–6.4 变化 → 重算 6.5」触发链。\n编号由原 v1.9 重排为 v1.0.9。"),
    ("v1.0.10", "archives/shooting-plan-workbench-v1.0.10.html",
     "§0.7 删除与 §1.1 重复的模特姓名输入框，摘要卡占满整行\n\n"
     "同步机制由双向改单向：模特资料唯一可编辑处是 §1.1，§0.7 纯只读回显。\n"
     "同时确立版本号规则：本地线统一用 1.0.x 续写。"),
    ("v1.0.11", "archives/shooting-plan-workbench-v1.0.11.html",
     "甘特图按时段显示上午/下午的黄金·蓝调时刻\n\n"
     "内置广州按 12 个月分档的黄金/蓝调时刻（solar_gen.py，NOAA 算法）；\n"
     "S8_SLOTS 改为 slotSet() 函数按拍摄时段取值；蓝调升为独立节点；\n"
     "§8.1 新增光影时刻手填覆盖区。\n"
     "修复节点标签时刻不显示与上午时段节点消失两个缺陷。"),
]


def fetch_blob(path):
    d = api("GET", "/contents/" + path, allow_404=True)
    if d is None:
        raise SystemExit("缺存档文件：%s" % path)
    return d["sha"]


def set_tag(ver, commit, note, minutes):
    """建 annotated tag（先删同名旧 tag，GitHub 不允许同名 ref 重复）。"""
    if api("GET", "/git/ref/tags/" + ver, allow_404=True) is not None:
        api("DELETE", "/git/refs/tags/" + ver)
        print("       删除时序错误的旧 tag %s" % ver)
    obj = api("POST", "/git/tags", {
        "tag": ver,
        "message": ("拍摄策划工作台 %s\n\n%s\n\n"
                    "tag 指向该版本存档入库的 commit，可直接 git diff 比对相邻版本。"
                    % (ver, note)),
        "object": commit, "type": "commit",
        "tagger": dict(AUTHOR, date=stamp(minutes)),
    })
    api("POST", "/git/refs", {"ref": "refs/tags/" + ver, "sha": obj["sha"]})


def main():
    print("=== 按正确时序重建 v1.0.7 ~ v1.0.11 ===\n")

    head = api("GET", "/git/ref/heads/" + BRANCH)["object"]["sha"]
    head_commit = api("GET", "/git/commits/" + head)
    if not head_commit["parents"]:
        raise SystemExit("HEAD无父 commit，无法构造链")
    parent = head_commit["parents"][0]["sha"]
    print("链起点（HEAD 的父 commit）: %s\n" % parent[:8])

    for i, (ver, path, note) in enumerate(CHAIN):
        blob = fetch_blob(path)
        base_tree = api("GET", "/git/commits/" + parent)["tree"]["sha"]
        tree = api("POST", "/git/trees", {"base_tree": base_tree, "tree": [
            {"path": path, "mode": "100644", "type": "blob", "sha": blob}]})
        commit = api("POST", "/git/commits", {
            "message": ("chore(%s): 版本存档快照入库\n\n%s\n\n"
                        "本 commit 只含本版存档文件，用于建立可按版本顺序比对的 tag 链。"
                        % (ver, note)),
            "tree": tree["sha"], "parents": [parent],
            "author": dict(AUTHOR, date=stamp(i * 10)),
            "committer": dict(AUTHOR, date=stamp(i * 10)),
        })["sha"]
        # 立刻打 tag —— tag 是 ref，能锚定 commit 不被 GC
        set_tag(ver, commit, note, i * 10 + 1)
        print("  ✓ %-9s %s  %s" % (ver, commit[:8], stamp(i * 10)[11:19]))
        parent = commit

    # 链尾 merge 回 main：双父保住 main 上并行会话的工作，文件内容零改动。
    # 注意：POST /git/trees 不接受空 tree 数组（报 Invalid tree info），
    # 而这里本来就不需要改任何文件 —— 直接复用 HEAD 的 tree sha 即可。
    head_tree = api("GET", "/git/commits/" + head)["tree"]["sha"]
    merge = api("POST", "/git/commits", {
        "message": ("chore(tags): 重建 v1.0.7 ~ v1.0.11 版本 tag 链\n\n"
                    "原 tag 时序等于「补录操作速度」而非版本先后（v1.0.11 早于 v1.0.7），\n"
                    "导致 git diff v1.0.10 v1.0.11 返回空。现按版本真实时序重建提交链，\n"
                    "tag 指向各自快照 commit，可直接比对相邻版本差异。\n\n"
                    "本 merge 提交不改动任何文件内容（复用 HEAD 的 tree），\n"
                    "只把版本链并回 main，以保住 main 上并行会话的工作成果。"),
        "tree": head_tree, "parents": [head, parent],
        "author": dict(AUTHOR, date=stamp(60)),
        "committer": dict(AUTHOR, date=stamp(60)),
    })["sha"]
    api("PATCH", "/git/refs/heads/" + BRANCH, {"sha": merge, "force": False})
    print("\nmerge %s 已快进到 main（文件内容零改动）" % merge[:8])
    print("完成。")


if __name__ == "__main__":
    main()