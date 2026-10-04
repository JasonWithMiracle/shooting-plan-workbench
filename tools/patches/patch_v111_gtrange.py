# -*- coding: utf-8 -*-
"""v1.0.11 补丁 E：修「选上午却看不到上午光影时刻」。

现象：把§0.2 拍摄时段切到「上午」，甘特轴上「上午黄金时刻 / 上午蓝调时刻」
两个节点**整段消失**（v1.0.11 专项 2 项FAIL）。

根因：gtRange() 的时间范围只按 8.2 表格行算——
  最早一行 08:30（妆造）→ T0 = 07:00
而上午黄金 06:37、蓝调 06:28 都落在 T0 之前，gtBlock 里
  if(m==null||m<T0||m>T1) return '';
就把这两个节点整段过滤掉了。

讽刺之处：这正是本需求的核心场景。选上午的用户恰恰要��看上午那组，
而它刚好落在轴的左边界之外——「块被裁掉」比「显示错」更难察觉。

修法：gtRange() 除了看行程行，还要把**当前时段对应的那两个光影节点**
纳入范围计算。只扩不缩——绝不能因为加了两个节点就把原本合适的轴拉宽。
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


rep("""function gtRange(){
  const arr=D.s8.行||[];
  let lo=Infinity, hi=-Infinity;
  arr.forEach(r=>{
    const m=t2m(r.时); if(m==null) return;
    lo=Math.min(lo,m);
    hi=Math.max(hi,m+(+r.耗时||0));
  });
  if(!isFinite(lo)){ lo=8*60; hi=20*60; }
  let T0=Math.floor((lo-60)/60)*60;
  let T1=Math.ceil((hi+60)/60)*60;
  while(T1-T0<360) T1+=60;
  return {T0,T1,span:T1-T0};
}""",
    """function gtRange(){
  const arr=D.s8.行||[];
  let lo=Infinity, hi=-Infinity;
  arr.forEach(r=>{
    const m=t2m(r.时); if(m==null) return;
    lo=Math.min(lo,m);
    hi=Math.max(hi,m+(+r.耗时||0));
  });
  if(!isFinite(lo)){ lo=8*60; hi=20*60; }
  /* v1.0.11：把当前时段对应的光影节点也纳入范围。
     起因：只按行程行算时，最早一行通常是妆造 08:30 → T0=07:00，
     而「上午黄金 06:37 / 上午蓝调 06:28」落在 T0 之前，
     被 gtBlock 的 m<T0 过滤掉 —— 结果「选上午却看不到上午那组光影」，
     恰好废掉了本需求的核心场景。
     只扩不缩：绝不能因为多了两个节点就把本来合适的轴拉宽。 */
  try{
    slotSet().forEach(sl=>{
      if(!/黄金时刻|蓝调时刻/.test(sl.k)) return;   /* 只看光影节点，流程节点不动轴 */
      const m=t2m(sl.t); if(m==null) return;
      lo=Math.min(lo,m); hi=Math.max(hi,m+30);      /* 蓝调/黄金按 30 分钟窗算右界 */
    });
  }catch(e){ /* slotSet 在 TDZ 时静默降级为「只看行程行」 */ }
  let T0=Math.floor((lo-60)/60)*60;
  let T1=Math.ceil((hi+60)/60)*60;
  while(T1-T0<360) T1+=60;
  return {T0,T1,span:T1-T0};
}""")

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用 %d 处，文件 %d 字符' % (n, len(s)))
