# -*- coding: utf-8 -*-
"""v1.0.11 补丁 B：把「光影时刻」区接进局部重绘链路 + 时段切换触发 + 事件委托。"""
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


# ── ① repaintGantt 增补：.solarbox 也要一起换 ──────────────────────────
rep("""  /* --- 8.1 甘特图：整块换掉（这里没有正在编辑的控件） --- */
  const old=sec.querySelector('.gt'); const box=document.createElement('div');
  box.innerHTML=gtBlock();
  const fresh=box.firstElementChild;
  if(old&&fresh) old.replaceWith(fresh);""",
    """  /* --- 8.1 甘特图：整块换掉（这里没有正在编辑的控件） --- */
  const old=sec.querySelector('.gt'); const box=document.createElement('div');
  box.innerHTML=gtBlock();
  const fresh=box.firstElementChild;
  if(old&&fresh) old.replaceWith(fresh);

  /* --- 8.1 v1.0.11：光影时刻覆盖区也要跟着重画。
     为什么单独处理：拍��时段（§0.2）或拍摄日期（§0.2）变化时，
     甘特轴上四个光影节点的**时刻与名称**都变（上午黄金 ↔ 下午黄金）。
     但 §0.2 在页面顶部，用户改的是那边的 select，不能整页 render()——
     那会销毁 §8 表格里正在编辑的 input。所以只换这两个块。--- */
  const oldS=sec.querySelector('.solarbox');
  if(oldS){
    const tb=document.createElement('div'); tb.innerHTML=solarOvrHtml();
    const fs=tb.firstElementChild;
    if(fs) oldS.replaceWith(fs);
  }""")

# ── ② patchLive 增补：时段/拍摄日期变化 → 重算光影时刻并重绘 §8 ─────────
rep("""  if(/^6\\.(器材|滤镜|灯|附件)\\.\\d+\\.(品|型|数|备)$/.test(p)) repaintGearTotal();
}""",
    """  if(/^6\\.(器材|滤镜|灯|附件)\\.\\d+\\.(品|型|数|备)$/.test(p)) repaintGearTotal();
  /* v1.0.11：拍摄日期 / 拍摄时段变化 → 甘特轴的光影节点要重算。
     此前 PERIODS（上午/下午/晚上）这个下拉压根没有代码消费它——
     §0.2 写着「决定行程表起止时间与日落窗口」，实际改了毫无影响。
     现在时段真正生效了：上午→取上午那组，下午/晚上→取下午那组。*/
  if(p==='0.拍摄日期'||p==='0.时段'){
    /* 先更新 8.1 里的星期提示（拍摄日期改动的原有行为） */
    repaintGantt();
  }
}""")

# ── ③ 事件委托：应用 / 清除手填覆盖 ────────────────────────────────────
rep("""/* 版本号同步：静态 HTML 里写了一份占位，这里再用 APP_VER 覆盖。""",
    """/* v1.0.11：光影时刻手填覆盖的两个按钮。
   不用 onclick 内联—— 事件委托挂一次，后续重绘换掉元素也不用重新绑定。*/
document.addEventListener('click', e=>{
  const ap=e.target.closest('[data-solar-apply]');
  const cl=e.target.closest('[data-solar-clear]');
  if(!ap&&!cl) return;
  e.preventDefault();
  if(cl){
    delete SOLAR_OVR[shotMonth()];
    saveSolarOverride();
    repaintGantt();
    toast('已清除' + shotMonth() + ' 月手填值，回落到内置表');
    return;
  }
  /* 应用：把四个区间里「起点填了」的项收进覆盖对象。
     终点留空时用起点 + 时长反推，避免出现 05:00→空白这种半截数据。 */
  const box=e.target.closest('.solarbox'); if(!box) return;
  const cur=SOLAR_OVR[shotMonth()]||{};
  const out={...cur};
  let any=false;
  ['amG','amB','pmG','pmB'].forEach(k=>{
    const a=box.querySelector('[data-solar="'+k+'0"]');
    const b=box.querySelector('[data-solar="'+k+'1"]');
    if(!a) return;
    const s0=(a.value||'').trim(), s1=(b&&b.value||'').trim();
    if(!s0&&!s1){ delete out[k]; return; }
    let end=s1;
    if(!end&&s0){
      const st=t2m(s0); /* 内置时长作为默认长度 */
      const base=(SOLAR[shotMonth()]||{})[k]||['00:00','00:00'];
      let len=(t2m(base[1])??0)-(t2m(base[0])??0); if(!len) len=30;
      end=m2t((st??0)+len);
    }
    out[k]=[s0||end,end]; any=true;
  });
  if(!any){ toast('还没有填任何时刻','warn'); return; }
  SOLAR_OVR[shotMonth()]=out; saveSolarOverride();
  repaintGantt();
  toast('已应用' + shotMonth() + ' 月手填的光影时刻');
});

/* 版本号同步：静态 HTML 里写了一份占位，这里再用 APP_VER 覆盖。""")

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用 %d 处替换，文件 %d 字符' % (n, len(s)))
