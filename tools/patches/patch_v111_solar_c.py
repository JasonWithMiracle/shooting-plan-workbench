# -*- coding: utf-8 -*-
"""v1.0.11 补丁 C：版本号升级 + 8.1 标题标注 + 打印时区说明。"""
import io

P = 'online.html'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
n = 0


def rep(old, new, cnt=1):
    global s, n
    c = s.count(old)
    assert c == cnt, '命中 %d 次（应为 %d）：%s' % (c, cnt, old[:70])
    s = s.replace(old, new)
    n += 1


# 版本号三处：APP_VER / <title> / 徽章占位
rep("const APP_VER='v1.0.10', TPL_VER='v3.0';",
    "const APP_VER='v1.0.11', TPL_VER='v3.0';")
rep("<title>拍摄策划工作台 v1.0.10</title>",
    "<title>拍摄策划工作台 v1.0.11</title>")
rep('id="verBadge">v1.0.10<',
    'id="verBadge">v1.0.11<')

# 8.1 标题：说明节点时刻的来源与可覆盖性
rep("""  <h3 id="anc-8-1">8.1 拍摄日甘特图<span class="rec" style="color:var(--amber)">可拖拽</span></h3>
  ${solarOvrHtml()}""",
    """  <h3 id="anc-8-1">8.1 拍摄日甘特图<span class="rec" style="color:var(--amber)">可拖拽</span></h3>
  ${solarOvrHtml()}
  <div class="sec-d" style="margin:0 0 8px">
    轴上带 <span style="color:#b8863f;font-weight:600">★</span> 的是<b>光影时刻节点</b>
    （黄金 / 蓝调），按你选的<b>拍摄时段</b>取对应那组，并随<b>拍摄日期</b>换算当月值。
    标注「参考」= 用的内置典型值，未在 8.2 排进行程；点击可在 8.2 里定位或新增该阶段。
  </div>""")

# 打印时区说明塞进 print 隐藏清单：光影时刻覆盖区在打印态应隐藏
# （它是编辑期工具，策划案打印件不需要让人手填时刻）
rep("""/* v1.0.9：原 §6.6「汇总条」.genbar / .gb 样式随「生成总清单」按钮一并移除。""",
    """/* v1.0.11：光影时刻手填覆盖区属编辑期工具，打印件里隐藏。
   与 .genbar 同理——策划案打出来给现场看，不需要让人回去填时刻。*/
@media print{.solarbox{display:none!important}}

/* v1.0.9：原 §6.6「汇总条」.genbar / .gb 样式随「生成总清单」按钮一并移除。""")

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用 %d 处替换，文件 %d 字符' % (n, len(s)))
