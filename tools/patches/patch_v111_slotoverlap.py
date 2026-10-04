# -*- coding: utf-8 -*-
"""v1.0.11 补丁 F：修节点标签重叠 + 图例文案过时。

问题1（视觉）：上午档时轴范围被拉到05:00–19:00，五个节点标签挤在
  06:28–08:30 这段里，文字互相压盖，糊成一团（见 shot_v111_am.png）。
  修法：给标签做**防重叠错位**——按顺序两两比较，若与前一个标签的
  左边界间距不足，则向下让开一行。标签是绝对定位，天然可以错位；
  配合一条细引线指回真实时刻，不丢准确性。

问题2（文案）：图例仍写「妆造/布光/拍摄/黄金时刻/日落/收工」，
  但 v1.0.11 已把节点改名为「上午/下午黄金时刻」「上午/下午蓝调时刻」，
  「日落」这个节点已不存在。改为动态生成，永远与实际节点一致。
"""
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


# ── ① 标签防重叠：记录已占用的左边界，重叠则换行让位 ────────────────────
rep("""  const slots=slotSet().map(sl=>{""",
    """  /* v1.0.11：节点标签防重叠。
     上午档时轴范围被拉到 05:00–19:00，五个标签全挤在 06:28–08:30 之间，
     文字互相压盖糊成一团。做法：按 x 顺序遍历，与上一个标签的右边界
     间距不足就往下让一行（标签绝对定位，天然可错位），并画一条细引线
     回到真实时刻—— 错位不丢准确性。 */
  const LABW=78;/* 标签近似宽度(px)，用于估算占位 */
  let lastRight=-1e9, lastLine=0;
  const slots=slotSet().map(sl=>{""")

rep("""    const w=Math.max(0,pct(m+60)-pct(m));
    return `<div class="gt-slot" style="left:${pct(m)}%;width:${w}%;--c:${sl.c}"></div>`
      +`<button class="gt-slotlab${linked?' linked':''}" data-slot="${esc(sl.k)}"
         style="left:calc(${pct(m)}% + 3px);--c:${sl.c}"
         title="${esc(sl.k+' '+label+'（'+(linked?'已与 8.2 联动':'典型参考值，未在 8.2 排入')+'）'
           +'\\n'+sl.tip+'\\n\\n点击：已排则定位到 8.2 对应行 / 未排则新增该阶段')}">`
        +`\\u2605 ${esc(sl.k)} ${esc(label)}${linked?'':'<i class="ref">参考</i>'}</button>`;
  }).join('');""",
    """    const w=Math.max(0,pct(m+60)-pct(m));
    /* 防重叠：估算该标签的像素左界，与上一个比较；不够就让到下一行 */
    const hostW=gtHostW();
    const px=pct(m)/100*hostW;
    let line=0;
    if(lastRight>-1e8 && px<lastRight+6) line=lastLine+1;
    lastRight=px+LABW; lastLine=line;
    const lead=line
      ? `<span class="gt-slotlab-lead" style="left:calc(${pct(m)}% + 2px);height:${line*14}px"></span>`
      : '';
    return `<div class="gt-slot" style="left:${pct(m)}%;width:${w}%;--c:${sl.c}"></div>`+lead
      +`<button class="gt-slotlab${linked?' linked':''}" data-slot="${esc(sl.k)}"
         style="left:calc(${pct(m)}% + 3px);top:${line*14}px;--c:${sl.c}"
         title="${esc(sl.k+' '+label+'（'+(linked?'已与 8.2 联动':'典型参考值，未在 8.2 排入')+'）'
           +'\\n'+sl.tip+'\\n\\n点击：已排则定位到 8.2 对应行 / 未排则新增该阶段')}">`
        +`\\u2605 ${esc(sl.k)} ${esc(label)}${linked?'':'<i class="ref">参考</i>'}</button>`;
  }).join('');""")

# gtHostW：读容器实际宽度（像素），供上面的换算用
rep("""function gtBlock(){""",
    """/* 甘特图容器的可用像素宽度（去掉滚动条余量），供标签防重叠换算 */
function gtHostW(){
  const el=document.querySelector('.gt');
  return el ? Math.max(280, el.clientWidth-14) : 900;
}
function gtBlock(){""")

# ── ② 标签 top 偏移样式 + 引线样式 ─────────────────────────────────────
rep(""".gt-slotlab:hover{opacity:1;background:var(--panel);box-shadow:0 1px 4px rgba(0,0,0,.14)}""",
    """.gt-slotlab:hover{opacity:1;background:var(--panel);box-shadow:0 1px 4px rgba(0,0,0,.14)}
/* v1.0.11：标签错位时用的引线，从轴顶拉到被挤下来的那一行 */
.gt-slotlab-lead{position:absolute;top:0;width:0;border-left:1px dashed currentColor;
  opacity:.45;z-index:3;pointer-events:none}
.gt-slotlab-lead{color:var(--text3)}""")

# ── ③ 图例文案：动态生成，永远与实际节点一致 ──────────────────────────
rep("""  <div class="hint">灰色竖条为<b>关键节点参考线</b>（妆造/布光/拍摄/黄金时刻/日落/收工），
  典型值仅供参考；<b>冬季日落早约 1 小时</b>，逆光剪影、氛围片都靠这两段。</div>""",
    """  <div class="hint" data-slot-legend>灰色竖条为<b>关键节点参考线</b>，典型值仅供参考。</div>""")

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用 %d 处，文件 %d 字符' % (n, len(s)))
