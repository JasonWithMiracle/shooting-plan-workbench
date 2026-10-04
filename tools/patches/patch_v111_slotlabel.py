# -*- coding: utf-8 -*-
"""v1.0.11 补丁 D：修既有缺陷 —— 节点标签的时刻在「未联动」时不显示。

发现方式：v1.0.11 专项验证 3 项 FAIL，追下去发现是 **v1.9 就存在的旧 bug**，
只是以前没被断言盯上（旧的节点名「黄金时刻」手输时刻看不出差别）。

根因（gtBlock 内的节点标签渲染）：
    const slotTime = slotActual(sl.k);       // 未在 8.2 排入时为 null
    const m       = t2m(slotTime || sl.t);  // ← 这里回落了，取值正确
    ...
    +`★ ${esc(sl.k)} ${esc(slotTime)}...`   // ← 这里没回落，输出 "null"
esc(null) 渲染成空字符串，所以标签**只显示节点名、缺时刻**；
而背景色块用 m 画在了正确位置 —— 于是「块对、字缺」，肉眼很容易放过。

修法：时刻统一用一个变量，两处共用。
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


rep("""  const slots=slotSet().map(sl=>{
    const slotTime=slotActual(sl.k);        /* 实际时刻（来自 8.2 行） */
    const m=t2m(slotTime||sl.t);
    const linked=slotTime!=null;
    if(m==null||m<T0||m>T1) return '';
    const w=Math.max(0,pct(m+60)-pct(m));
    return `<div class="gt-slot" style="left:${pct(m)}%;width:${w}%;--c:${sl.c}"></div>`
      +`<button class="gt-slotlab${linked?' linked':''}" data-slot="${esc(sl.k)}"
         style="left:calc(${pct(m)}% + 3px);--c:${sl.c}"
         title="${esc(sl.k+' '+slotTime+'（'+(linked?'已与 8.2 联动':'典型参考值，未在 8.2 排入')+'）'
           +'\\n'+sl.tip+'\\n\\n点击：已排则定位到 8.2 对应行 / 未排则新增该阶段')}">`
        +`\\u2605 ${esc(sl.k)} ${esc(slotTime)}${linked?'':'<i class="ref">参考</i>'}</button>`;
  }).join('');""",
    """  const slots=slotSet().map(sl=>{
    /* v1.0.11 修既有缺陷：时刻必须在**一处**决定，绘图与标签文字共用。
       原来绘图用 slotTime||sl.t（正确），标签却直接用 slotTime，
       未与 8.2 联动时它是 null → 标签只显示节点名、缺时刻，
       而背景块画在正确位置 —— 「块对字缺」，肉眼极易放过。 */
    const linked=slotActual(sl.k)!=null;
    const label =slotActual(sl.k) || sl.t;   /* 实际时刻，未联动则用典型值 */
    const m=t2m(label);
    if(m==null||m<T0||m>T1) return '';
    const w=Math.max(0,pct(m+60)-pct(m));
    return `<div class="gt-slot" style="left:${pct(m)}%;width:${w}%;--c:${sl.c}"></div>`
      +`<button class="gt-slotlab${linked?' linked':''}" data-slot="${esc(sl.k)}"
         style="left:calc(${pct(m)}% + 3px);--c:${sl.c}"
         title="${esc(sl.k+' '+label+'（'+(linked?'已与 8.2 联动':'典型参考值，未在 8.2 排入')+'）'
           +'\\n'+sl.tip+'\\n\\n点击：已排则定位到 8.2 对应行 / 未排则新增该阶段')}">`
        +`\\u2605 ${esc(sl.k)} ${esc(label)}${linked?'':'<i class="ref">参考</i>'}</button>`;
  }).join('');""")

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用 %d 处，文件 %d 字符' % (n, len(s)))
