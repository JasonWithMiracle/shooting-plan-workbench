# 版本与 tag 管理规范

本项目的版本管理标准**沿用过往一般性任务的标准**（参见 VoiceDesk 仓库的
`CONTRIBUTING.md`），不因本项目另起一套。

---

## 一、三条硬规矩

| 规矩 | 内容 | 为什么 |
| --- | --- | --- |
| **1. tag 必须 annotated** | `git tag -a`，不能只打裸指针 | lightweight tag 没有版本说明、无tagger，在 Releases 里不可追溯，等于没打 |
| **2. tag 时序 = 版本时序** | tag 的 commit 必须按版本先后严格递增 | 时序错乱会让 `git diff v1.0.10 v1.0.11` 返回空，tag 形同虚设 |
| **3. tag 三件套齐平** | 每个 tag 都有：tag 对象 + `archives/` 版本存档 + `CHANGELOG.md` 段落 | 三者任缺其一都无法回溯「这一版到底改了什么」 |

校验命令：

```bash
python git_release.py verify
```

---

## 二、版本号规则

遵循[语义化版本](https://semver.org/lang/zh-CN/)：`MAJOR.MINOR.PATCH`，前缀 `v`。

###⚠️ 本项目有一处历史例外：编号重排

2026-10-04 之前存在两条互不相干的版本线，已于v1.0.10 拍板并轨：

| 来源 | 原编号 | 现编号 |
| --- | --- | --- |
| 文件记录线（前段） | v1.0.0 ~ v1.0.2、v1.1.0 | **不变**，已发布不改号 |
| 本地文件线（后段） | v1.7、v1.8、v1.9 | v1.0.7、v1.0.8、v1.0.9 |

**后果**：`1.0.11` 在数字上小于 `1.1.0`，但时间上更晚。

> **比较版本新旧请以 tag 的时间戳为准，不要只看数字大小。**

这条说明同时写进了 `v1.1.0` 的 tag 说明里，避免日后误判。

---

## 三、目录结构

```
/
├── online/index.html          GitHub Pages 线上版（部署目标，勿手改）
├── src/online.html            代码源文件（唯一可编辑处）
├── archives/                  版本存档，文件名带版本号，tag 比对的依据
│   └── shooting-plan-workbench-v1.0.11.html
├── docs/                      使用文档
├── screenshots/               功能截图
├── tools/                     版本治理工具（本目录）
├── CHANGELOG.md               变更记录，每版一段
└── CONTRIBUTING.md            协作与提交规范
```

**`online/index.html` 与 `src/online.html` 必须同源** —— 前者由后者生成，
不要直接改线上那份，否则下次同步会被覆盖。

---

## 四、日常操作

### 发布一个新版本

```bash
# 1. 改src/online.html，把 APP_VER 改成新版本号（版本号单一事实源）
# 2. 发布前检查 —— 不通过会拒绝发布
python tools/git_release.py plan-v v1.0.12

# 3. 补CHANGELOG.md 的新版本段
# 4. 发布（推代码快照 + 版本存档 + 打 annotated tag，三件事一起做）
python tools/git_release.py tag v1.0.12 "提交说明"
```

### 比对两个版本

```bash
# 看某两版的实际代码差异
python tools/git_release.py diff v1.0.10 v1.0.11

# 看 tag 清单及说明
python tools/git_release.py tag-list

# 校验三件套一致性
python tools/git_release.py verify
```

GitHub 上直接比对（浏览器）：

```
https://github.com/JasonWithMiracle/shooting-plan-workbench/compare/v1.0.10...v1.0.11
```

---

## 五、⚠️ 本项目的特殊约束：git 协议层不可用

**实测结论**（2026-10-05）：

| 通道 | 结果 |
| --- | --- |
| `git push` / `git fetch`（走代理） | ❌ `CONNECT tunnel failed, 502` |
| `git push` / `git fetch`（直连） | ❌ `Failed to connect to github.com:443` |
| `curl` 走同一代理 | ✅ 200 |
| **GitHub REST API** | ✅ 完全可用 |

沙箱内 git 的 smart HTTP 需要先发 `CONNECT` 建隧道，而本机代理对该隧道返502；
直连则被网络阻断。**所以本项目所有远端写操作走 REST API，不用 git push。**

这也是 `tools/` 下全是 Python 脚本而非 shell 脚本的原因。

###由此产生的两条纪律

1. **不要用 `git push`**，会失败。改用 `python tools/git_release.py tag <版本> "<说明>"`。
2. **建 commit 后立刻打 tag 或挂到分支** —— GitHub 会GC 掉不被任何 ref 引用的对象。
   本项目真踩过这个坑：先建链、最后才打 tag，中途5 个 commit 全部被回收（直读404）。

### 404 的两种含义

GitHub 对「资源不存在」和「无权限」都返 404，只能靠路径语义区分：

| 路径 | 404 含义 | 处理 |
| --- | --- | --- |
| `/contents/<path>` | 文件不存在 | 容忍，转新建 |
| `/git/ref/tags/<tag>` | tag 尚未创建 | 容忍 |
| 其他（仓库、分支） | 配置错误 | **必须中止** |

`git_release.py` 里的 `allow_404` 参数就是干这个的，别无脑吞掉所有 404。

### 其他 API 坑

| 坑 | 表现 | 正解 |
| --- | --- | --- |
| DELETE 返回 204 空 body | `json.loads('')` 崩，**但操作其实成功了** | 先判空再解析 |
| `POST /git/trees` 传空 `tree` 数组 | `422Invalid tree info` | 直接复用已有 tree sha |
| `POST /git/trees` 的 `base_tree` | 传 commit sha 会 422 | 必须传 **tree** sha |

---

## 六、提交规范

采用 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)：

```
<type>(<scope>): <subject>

<body>
```

| type | 含义 |
| --- | --- |
| `feat` | 新功能 |
| `fix` | 缺陷修复 |
| `docs` | 文档 |
| `refactor` | 重构（不改行为） |
| `chore` | 杂项（版本快照、打 tag 等） |

**subject 用中文，不超过 50 字，句末不加句号；body 写「为什么改」，不是「改了什么」**（diff 已说明后者）。

示例：

```
fix(v1.0.9): 修复 6.5 器材总表不实时刷新

6.1–6.4 变化后6.5 始终不出现。根因是 patchLive() 只处理「红框清除 /
灯位功率 / 甘特图重算」，没有任何「6.1–6.4 变化 → 重算 6.5」的触发链，
6.5 只在首绘时算一次。

新增 repaintGearTotal() 只替换 6.5 的 innerHTML，不重建 6.1–6.4 的 input
（否则输入框失焦，用户打字会断）。
```

---

## 七、`.gitignore` 纪律

**禁止写不加锚点的 `_*`。**

```gitignore
_*        # ← 危险：会吞掉子目录里所有下划线开头的正常文件
```

被吞的文件**在 `git status` 里根本不出现**，属于静默失败。
正确写法是锚定到根目录：`/_*`（只匹配根目录，不碰子目录）。

排查手法：用临时仓库跑 `git add -A -n`（dry-run）数一遍入库文件，
对比改动前后的数量与清单 —— **只看 `git status` 是不够的**。