# -*- coding: utf-8 -*-
"""v1.0.11 补丁 C（续）：8.1 标题说明 + 打印隐藏光影覆盖区。"""
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


rep('''  <h3 id="anc-8-1">8.1 拍摄日甘特图<span class="rec" style="color:var(--amber)">可拖拽</span></h3>
  ${solarOvrHtml()}''',
    '''  <h3 id="anc-8-1">8.1 拍摄日甘特图<span class="rec" style="color:var(--amber)">可拖拽</span></h3>
  ${solarOvrHtml()}
  <div class="sec-d" style="margin:0 0 8px">
    轴上带 <span style="color:#b8863f;font-weight:600">★</span> 的是<b>光影时刻节点</b>
    （黄金 / 蓝调），按你选的<b>拍摄时段</b>取对应那组，并随<b>拍摄日期</b>换算当月值。
    标注「参考」= 用的内置典型值，未在 8.2 排进行程；点击可在 8.2 里定位或新增该阶段。
  </div>''')

# 打印隐藏：锚点用 @media print 已有的隐藏清单里加一行
rep('''/* 核对态 / 打印：甘特图无交互，只作为静态示意 */''',
    '''/* v1.0.11：光影时刻手填覆盖区属编辑期工具，打印件里隐藏。
   与 .genbar 同理——策划案打出来给现场看，不需要让人回去填时刻。*/
@media print{.solarbox{display:none!important}}

/* 核对态 / 打印：甘特图无交互，只作为静态示意 */''')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用 %d 处，文件 %d 字符' % (n, len(s)))
