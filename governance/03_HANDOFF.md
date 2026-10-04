---
type: handoff
created: 2026-10-04
updated: 2026-10-04
status: active
priority: P0
---

# 03 · 交接 HANDOFF

> 每次会话/阶段收尾写一条。**最新一条在最上方。**
> 目的：任何人一进来（尤其是换了会话的我）读完这一页就知道现在在哪、下一步做什么、哪些坑别踩。

---

## H-002 · 2026-10-04 18:12 · 治理文档层上传云端完成

### 背景
Jason 追加要求：README 上传云盘，且台账/索引/说明/roadmap/handoff 等治理类文档统一放该文件夹并**置于最高优先级、方便浏览检索**。

### 已完成
1. 建立**治理文档层（P0置顶）**，用 `00_`~`03_` 数字前缀保证按名称排序恒在最前：
   - `00_总索引.md`（`EbUJeKeJReSf`）— 唯一入口
   - `01_台账.md`（`EaPEzWOJVlkB`）— 唯一记账处
   - `02_ROADMAP.md`（`ECJxxgZAANhh`）— 阶段 M0~M3
   - `03_HANDOFF.md`（`EsBjmzXEwYvy`）— 交接记录
   - `README.md`（`ElmMhflnVyen`）— 归档规范说明（已覆盖为v02，含治理层导航）
2. 全部 5 份已上传云端，**云端目录排序实测为 00→01→02→03→README**，符合置顶要求。
3. 更新台账：补齐 5 份文件的 file_id、版本、大小；风险项改为「云端 size 显示 0（可忽略）」。
4. 更新 roadmap：M1 标记完成，下一步清单去掉「等确认上传」项。

### 下一步（给下一棒）
1. Jason 拍板：本地路径是否从一次性工作区 `2026-10-04-18-01-48` 迁到 vault 固定位置（**唯一悬而未决项**）。
2. Jason 给出首个真实拍摄项目 → 在 `01_台账.md` 登记，启动 M2。
3. 每次会话收尾必须：更新 `03_HANDOFF.md`（新条目置顶）+ `01_台账.md` + `02_ROADMAP.md`。

### 坑与注意（重要，务必复用）
- **网盘上传三步缺一不可**：`file_upload` 取临时 URL → `curl -T` PUT → `file_upload_complete`。只做前两步文件不落库。
- **`file_upload` 的 `labels` 参数会报校验失败**（传数组仍提示 must be array）→ **直接省略该参数**。
- **长 header 绝不能内联在 bash 命令行**：`Authorization` + `x-cos-security-token` 合计上千字符，内联会被 shell 截断导致 `403 InvalidAccessKeyId`。**必须写入文件**。已验证可行方案：`.workbuddy/nd_put.py`（Python subprocess 调 curl，header 从 spec.json 读）。本次 5 次上传中前 4 次内联/手写脚本有2 次踩坑，改用 Python 脚本后 100% 成功。
- 临时签名有效期约 2 小时，失败就重新调 `file_upload` 取新 URL，别复用。
- 上传成功后删掉临时 spec json 与脚本，别留在 `.workbuddy/`。
- 云端 dir_id 固定 `EuTsQCemoDEk`；`file_id` 复用同名覆盖时保持不变（如 README 始终 `ElmMhflnVyen`）。
- 云端 `size` 字段返回 0 是元数据表现，不代表上传失败，以 HTTP 200 + complete 返回为准。

---

## H-001 · 2026-10-04 18:05 · 归档规范与治理层建立

### 背景
Jason 要求：本地与云端产生的所有「拍摄策划工作台」相关文档统一放在同名文件夹下，且台账/索引/说明/roadmap/handoff 需置顶、便于浏览检索。

### 已完成
1. 确认三项决策：本地目录=工作区根同名文件夹；上传=先本地→确认→再上云；云端=扁平单层。
2. 新建本地目录 `拍摄策划工作台/`，写入 `README.md`（归档规范 + 命名规范 `项目名_内容类型_版本_YYYYMMDD.ext` + 8 类内容分类）。
3. 建立治理文档层（P0，数字前缀保证排序置顶）：
   - `00_总索引.md` — 唯一入口，一页总览
   - `01_台账.md` — 唯一记账处（项目/任务/文件/决策/风险）
   - `02_ROADMAP.md` — 阶段 M0~M3 + 下一步清单
   - `03_HANDOFF.md` — 本文件
4. `README.md` 已上传云端 → `拍摄策划工作台/`，file_id `ElmMhflnVyen`。

### 当前状态
- 本地：5 份文件齐备（README + 00~03）。
- 云端：仅 README 一份，00~03 **待 Jason 确认后上传**。

### 下一步（给下一棒）
1. 问 Jason：00~03 是否上传云端 → 得到确认后逐个上传（流程见下方「上传操作要点」）。
2. 问 Jason：本地路径是否从一次性工作区 `2026-10-04-18-01-48` 迁到 vault 固定位置。
3. Jason 给出首个真实拍摄项目后，在 `01_台账.md` 登记并启动 M2。

### 坑与注意（重要）
- **网盘上传必须三步**：`file_upload` 取临时 URL → `curl -T` PUT → `file_upload_complete`。只做前两步文件不会出现在网盘。
- **`file_upload` 的 `labels` 参数传数组会报校验失败**（提示 must be array 但仍失败），**直接省略该参数**。
- **临时签名有效期约 2 小时**，失败就重新调`file_upload` 取新 URL，别复用旧的。
- 上传脚本里 `Authorization` 与 `x-cos-security-token` 极长，**必须用脚本文件承载变量**，直接在命令行内联会被 shell 截断/转义出错（第一次尝试即因内联导致 403 InvalidAccessKeyId）。
- 上传成功后记得 `rm` 掉临时脚本，不要留在 `.workbuddy/` 里污染。
- 云端 dir_id 固定为 `EuTsQCemoDEk`，每次调用都要带。

### 上传操作要点（复用）
1. `stat -c%s本地文件` 取字节数
2. `file_upload(dir_id, file_name, file_size, conflict_strategy='overwrite')` →拿 domain/path/headers/task_id/confirm_key
3. 写临时 sh 脚本承载 headers → `curl -sS -X PUT ... -T本地文件URL`，期望 `HTTP_CODE:200`
4. `file_upload_complete(dir_id, file_name, file_size, task_id, confirm_key)` → 返回 file_id
5. 清理临时脚本

---

## 变更历史

| 交接号 | 日期 | 摘要 |
| --- | --- | --- |
| H-002 | 2026-10-04 | 治理文档层 00~03 上传云端，实测排序置顶；沉淀 Python 上传脚本 |
| H-001 | 2026-10-04 | 建立归档规范 + 治理文档层，上传 README |
