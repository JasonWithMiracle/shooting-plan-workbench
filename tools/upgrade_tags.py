# -*- coding: utf-8 -*-
"""把 lightweight tag 原地转换为 annotated tag（commit sha 不变）。

为什么需要：lightweight tag 只是给 commit 加个指针，不带版本说明，
在 GitHub Releases 里没有描述、无法追溯发布意图。
annotated tag 是独立对象，可带 tagger 与说明，是可审计的发布凭据。

安全性：转换前后的 commit sha 完全相同 —— 代码历史一个字节都不动，
只把「裸指针」换成「带说明的对象」。这是 tag 的正常演进方式，
不是重写历史（重写历史指force push 改commit，那是另一回事）。

已核对：v1.0.0 -> b4b740de（release: v1.0.0 首个里程碑版本）
        v1.1.0 -> fa8fe339（release: v1.1.0 存储加固）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_release import api  # noqa: E402

UPGRADE = {
    "v1.0.0": (
        "拍摄策划工作台 v1.0.0 — 首个里程碑版本\n\n"
        "单文件离线拍摄策划工作台，12 章节全部做实，零外部依赖。\n\n"
        "- 编号自动分配 CX-YYYYMMDD-XX（只读、跨日重置、释放不撞号）\n"
        "- 模特库 / 场地库本地持久化 + CSV 导出\n"
        "- 布光双模式（严谨含 3D 渲染图 / 快捷整节不显示）\n"
        "- 拍摄日时段轴（含黄金时刻与日落）+ timetable + 耗时校验\n"
        "- 字段级强制项校验，顶栏完成度与导出拦截三处联动\n"
        "- 深浅主题 + 打印样式适配\n\n"
        "技术指标：单文件 114 KB / 2157 行 · 外部依赖 0 · 246 项 Playwright 断言全通过\n"
        "许可：MIT\n\n"
        "本 tag 由 lightweight 原地转换为 annotated，指向的 commit 未变。"
    ),
    "v1.1.0": (
        "拍摄策划工作台 v1.1.0 — 存储加固\n\n"
        "- 修复：存储写满时界面无提示、修改未落库（save() 统一捕获 QuotaExceededError）\n"
        "- 改进：图片改为按目标体积自适应压缩（<=160KB/张），iPhone 原图 98KB -> 19KB\n"
        "- 新增：顶栏存储占用指示条（75% 黄 / 90% 红）\n"
        "- 文档：更正此前「4.94MB / 触顶全丢」的错误口径（实测为 4MB、仅新数据未写入）\n"
        "- 移除：自实现 QR 编码器（该需求前提不成立，数据从未离开浏览器）\n\n"
        "测试：357 项断言全部通过（289 + 35 + 21 + 12）\n\n"
        "版本号说明：1.1.0 数字上大于后续的 1.0.7~1.0.11，但时间上更早 —— "
        "这是历史编号重排的结果（详见 CHANGELOG v1.0.10 段「两条线并轨说明」），"
        "比较版本新旧请以 tag 的时间戳为准，不要只看数字大小。\n\n"
        "本 tag 由 lightweight 原地转换为 annotated，指向的 commit 未变。"
    ),
}


def _now_iso():
    import datetime
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def upgrade(name, message):
    ref = api("GET", "/git/ref/tags/" + name, allow_404=True)
    if ref is None:
        print("· %s 当前不存在，视为待补录（跳过转换）" % name)
        return
    if ref["object"]["type"] == "tag":
        print("· %s 已是 annotated，跳过" % name)
        return
    commit_sha = ref["object"]["sha"]
    print("%s 当前为 lightweight，指向 commit %s" % (name, commit_sha[:8]))

    # 先建annotated 对象并落ref，再删不用的旧指针。
    # GitHub 不允许同名 ref 重复创建，所以顺序只能是：
    # 建对象 → 删ref → 建 ref。若中途失败，ref 可能短暂缺失，
    # 因此对象必须先建好（建对象是幂等的，不依赖 ref）。
    tag_obj = api("POST", "/git/tags", {
        "tag": name, "message": message, "object": commit_sha, "type": "commit",
        "tagger": {"name": "JasonWithMiracle",
                    "email": "122904020+JasonWithMiracle@users.noreply.github.com",
                    "date": _now_iso()},
    })
    api("DELETE", "/git/refs/tags/" + name)
    api("POST", "/git/refs", {"ref": "refs/tags/" + name, "sha": tag_obj["sha"]})

    check = api("GET", "/git/ref/tags/" + name, allow_404=True)
    if check is None:
        raise SystemExit("✗ %s 转换后 ref 丢失，需手工恢复（对象 %s仍在）"
                         % (name, tag_obj["sha"]))
    same = api("GET", "/git/tags/" + check["object"]["sha"])["object"]["sha"]
    if same != commit_sha:
        raise SystemExit("✗ commit 漂移：%s != %s" % (same[:8], commit_sha[:8]))
    print("✓ %s 已转为 annotated，commit 保持 %s（未变）\n" % (name, commit_sha[:8]))


def main():
    print("=== lightweight → annotated 转换 ===")
    for name, msg in UPGRADE.items():
        upgrade(name, msg)
    print("完成。commit 历史未改动。")


if __name__ == "__main__":
    main()