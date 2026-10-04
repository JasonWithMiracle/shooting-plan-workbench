# -*- coding: utf-8 -*-
"""v1.0.11：甘特图按时段显示上午/下午的黄金·蓝调时刻。

背景：此前 S8_SLOTS 写死一组典型值（全站只有「黄金时刻 16:30」+「日落 18:30」，
蓝调只是日落的 tip 文案），且PERIODS 下拉（上午/下午/晚上）压根没有代码消费它——
§0.2 的 hint 写着「决定行程表起止时间与日落窗口」是空头承诺。

本版做四件事：
  ① 内置广州 12 档（按月份）黄金/蓝调时刻表，由 solar_gen.py 用 NOAA 算法算，
     口径与 miniwebtool 一致：黄金=高度角+6°~-4°，蓝调=-4°~-6°
  ② S8_SLOTS 改为**函数生成**（slotSet()）：按 D.s0.时段 取上午档或下午档
  ③ 蓝调升为独立节点，四节点：上午黄金 → 上午蓝调 → 下午黄金 → 下午蓝调
  ④ §8.1 加「光影时刻」手填覆盖区，用户填了就用用户的（优先于内置表）

用户拍板的四项（2026-10-04）：
  q-0 内置查表 + 允许手填覆盖
  q-1 按月份分12 档
  q-2 只改黄金/蓝调节点（不动妆造/布光/拍摄/收工）
  q-3 上午黄金/上午蓝调/下午黄金/下午蓝调 四节点
"""
import io

P = 'online.html'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
n = 0


def rep(old, new, cnt=1):
    """幂等替换：命中数不符即中止不写盘。"""
    global s, n
    c = s.count(old)
    assert c == cnt, '命中 %d 次（应为 %d）：%s' % (c, cnt, old[:70])
    s = s.replace(old, new)
    n += 1


# ── ① 内置光影表 + slotSet() + 覆盖读取 ────────────────────────────────
OLD_SLOTS = """/* §8 行程安排（v1.6 做实）：timetable 行数组 + 特殊时段标记。
   甘特时段轴的「黄金时刻 / 日落」按**季节**给出典型值（北京时间），
   实际日落时刻受纬度与具体日期影响，需以拍摄地实测为准，故标注为参考值。 */
const S8_SLOTS=[
  {k:'妆造',  t:'08:30',  seg:'prep',  c:'#7d8a76',
   tip:'化妆 / 换装 / 妆面参考图确认'},
  {k:'布光',  t:'10:00',  seg:'setup', c:'#8a8467',
   tip:'架灯、测光、确认 §7 布光方案落地'},
  {k:'拍摄',  t:'12:00',  seg:'shoot', c:'#8a7b68',
   tip:'正片拍摄，按 §11 参考样片对齐风格'},
  {k:'黄金时刻', t:'16:30', seg:'golden', c:'#b8863f',
   tip:'★ 低角度暖光，逆光/剪影最佳时段'},
  {k:'日落',  t:'18:30',  seg:'sunset', c:'#a05a4a',
   tip:'★ 蓝调时刻，日落后 30 分钟内'},
  {k:'收工',  t:'19:30',  seg:'wrap',  c:'#6f7d8a',
   tip:'归还场地物品、向管理员致谢'}
];"""

NEW_SLOTS = """/* ==========================================================================
   §8.1 甘特时段轴的关键节点
   --------------------------------------------------------------------------
   v1.0.11 变更（用户需求：每天黄金/蓝调时刻都不同，上午和下午各有一组，
   拍摄时段选上午就显示上午那组，下午/晚上就显示下午那组）：

   此前这里写死一组全年通用值（全站只有「黄金时刻 16:30」+「日落 18:30」，
   蓝调仅是日落节点 tip 里的一句文案），而 §0.2 的 PERIODS 下拉
   （上午/下午/晚上）压根没有任何代码消费它——填了也不影响甘特图。

   现在改成三件事：
     ① SOLAR 表：广州（23.13°N/113.26°E）按 12 个月分档的日出/日落/
        上午黄金/上午蓝调/下午黄金/下午蓝调。每月取 15 日为该月代表值。
        由 solar_gen.py 用 NOAA 简化太阳位置算法算出，口径与
        miniwebtool 黄金蓝调计算器一致：
           日出日落= 高度角 -0.833°（含大气折射 + 太阳圆盘半径）
           黄金时刻  = 高度角 +6° ~ -4°
           蓝调时刻  = 高度角 -4° ~ -6°（民用晨昏蒙影下段）
        实测广州全年日长10.7~13.6 小时，6 月最长、1 月最短，符合预期。
        ⚠️ 若拍摄地不是广州，务必在下方「光影时刻」区按当地数据手填覆盖。
     ② slotSet()：按 D.s0.时段 取对应那组。时段未选时默认用下午档
        （多数人下午拍，且下午那组信息量最大）。
     ③ 覆盖优先：用户在 §8.1「光影时刻」区手填的值 > 内置表。
   --------------------------------------------------------------------------
   节点顺序：上午黄金 → 上午蓝调 →（白天）→ 下午黄金 → 下午蓝调。
   蓝调从「日落的 tip 文案」升为独立节点—— 摄影上它是独立的拍摄窗口，
   需要单独的曝光参数（三脚架 + 长曝），不该藏在别的节点说明里。 */
const SOLAR={
  1:{sr:'06:52',ss:'17:44',amG:['06:37','07:25'],amB:['06:28','06:37'],pmG:['17:11','17:59'],pmB:['17:59','18:08']},
  2:{sr:'06:31',ss:'17:54',amG:['06:17','07:02'],amB:['06:08','06:17'],pmG:['17:23','18:08'],pmB:['18:08','18:17']},
  3:{sr:'06:18',ss:'18:17',amG:['06:04','06:47'],amB:['05:55','06:04'],pmG:['17:47','18:31'],pmB:['18:31','18:40']},
  4:{sr:'06:06',ss:'18:47',amG:['05:52','06:37'],amB:['05:44','05:52'],pmG:['18:17','19:01'],pmB:['19:01','19:10']},
  5:{sr:'05:54',ss:'19:08',amG:['05:39','06:25'],amB:['05:29','05:39'],pmG:['18:37','19:23'],pmB:['19:23','19:32']},
  6:{sr:'05:40',ss:'19:13',amG:['05:25','06:13'],amB:['05:15','05:25'],pmG:['18:41','19:29'],pmB:['19:29','19:39']},
  7:{sr:'05:38',ss:'19:04',amG:['05:23','06:10'],amB:['05:13','05:23'],pmG:['18:32','19:19'],pmB:['19:19','19:29']},
  8:{sr:'05:54',ss:'18:51',amG:['05:39','06:24'],amB:['05:30','05:39'],pmG:['18:20','19:05'],pmB:['19:05','19:14']},
  9:{sr:'06:23',ss:'18:41',amG:['06:09','06:53'],amB:['06:00','06:09'],pmG:['18:11','18:55'],pmB:['18:55','19:03']},
 10:{sr:'06:52',ss:'18:31',amG:['06:38','07:22'],amB:['06:30','06:38'],pmG:['18:00','18:45'],pmB:['18:45','18:53']},
 11:{sr:'07:11',ss:'18:13',amG:['06:56','07:43'],amB:['06:47','06:56'],pmG:['17:41','18:28'],pmB:['18:28','18:37']},
 12:{sr:'07:10',ss:'17:53',amG:['06:55','07:43'],amB:['06:45','06:55'],pmG:['17:20','18:08'],pmB:['18:08','18:18']}
};
/* 手填覆盖的存储键（localStorage，不进 D——它是「工具侧的参考数据」，
   不是策划案内容，不该跟着整案导出/导入走） */
const LS_SOLAR_OVR='sw_solar_override';
let SOLAR_OVR={};
try{ SOLAR_OVR=JSON.parse(localStorage.getItem(LS_SOLAR_OVR)||'{}')||{}; }catch(e){ SOLAR_OVR={}; }
/* 覆盖值结构：{amG:['06:40','07:30'],amB:[...],pmG:[...],pmB:[...],sr:'',ss:''}
   支持只填其中几项，未填的项回落到内置表。 */
function solarOverride(){
  return SOLAR_OVR[shotMonth()]||null;
}
function shotMonth(){
  const d=String(D.s0.拍摄日期||'').match(/(\\d{4})-(\\d{2})/);
  return d? +d[2] : new Date().getMonth()+1;
}
function solarFor(m){
  return SOLAR[m]||SOLAR[1];
}
function saveSolarOverride(){
  try{ localStorage.setItem(LS_SOLAR_OVR,JSON.stringify(SOLAR_OVR)); }catch(e){}
}
/* 时段 → 取上午档还是下午档。用户拍板：「选上午显示上午那组，
   选下午、晚上都显示下午那组」（晚上没有太阳，自然取下午那组）。 */
function solarHalf(){
  return String(D.s0.时段||'').trim()==='上午' ? 'am' : 'pm';
}
/* 取出某档的四个时刻，已合并手填覆盖 */
function solarTimes(){
  const m=shotMonth(), base=solarFor(m), ov=solarOverride(), half=solarHalf();
  const pick=k=> (ov&&Array.isArray(ov[k])&&ov[k][0]) ? ov[k] : base[k];
  return { sr: (ov&&ov.sr)||base.sr, ss: (ov&&ov.ss)||base.ss,
           amG:pick('amG'), amB:pick('amB'), pmG:pick('pmG'), pmB:pick('pmB'), half, month:m };
}
/* S8_SLOTS 改函数生成：前三个（妆造/布光/拍摄）与收工是**流程节点**，
   保持原样；四个光影节点按时段与月份动态取时刻。 */
function slotSet(){
  const T=solarTimes();
  const am=T.half==='am';
  return[
    {k:'妆造',  t:'08:30',seg:'prep',  c:'#7d8a76',
     tip:'化妆 / 换装 / 妆面参考图确认'},
    {k:'布光',  t:'10:00',seg:'setup', c:'#8a8467',
     tip:'架灯、测光、确认 §7 布光方案落地'},
    {k:'拍摄',  t:'12:00',seg:'shoot', c:'#8a7b68',
     tip:'正片拍摄，按 §11 参考样片对齐风格'},
    {k:am?'上午黄金时刻':'下午黄金时刻', t:am?T.amG[0]:T.pmG[0], seg:'golden', c:'#b8863f',
     tip:'★ 黄金时刻（太阳高度角 +6°~-4°）：低角度暖光，'
        +'色温约 3000-4000K，逆光/剪影/轮廓光最佳时段'
        +'\\n本组为广州 ' + T.month + ' 月参考值（持续到 ' + (am?T.amG[1]:T.pmG[1]) + '）'},
    {k:am?'上午蓝调时刻':'下午蓝调时刻', t:am?T.amB[0]:T.pmB[0], seg:'sunset', c:'#a05a4a',
     tip:'★ 蓝调时刻（太阳高度角 -4°~-6°，民用晨昏蒙影）：冷调天空，'
        +'需三脚架 + 长曝，人工灯光与天光亮度接近'
        +'\\n本组为广州 ' + T.month + ' 月参考值（持续到 ' + (am?T.amB[1]:T.pmB[1]) + '）'},
    {k:'收工',  t:'19:30', seg:'wrap',  c:'#6f7d8a',
     tip:'归还场地物品、向管理员致谢'}
  ];
}
/* 手填覆盖表单：填了就用用户的，没填回落内置表。 */
function solarOvrHtml(){
  const T=solarTimes(), m=shotMonth(), base=solarFor(m);
  const ov=solarOverride()||{};
  const halfTxt=T.half==='am' ? '上午档' : '下午档（时段选了下午或晚上）';
  const f=(key,label,baseVal,ph)=>{
    const v=(ov&&Array.isArray(ov[key])&&ov[key][0])?ov[key][0]:'';
    return `<div class="f" style="margin:0">
      <label>${label}</label>
      <div style="display:flex;gap:6px;align-items:center">
        <input type="time" data-solar="${key}0" value="${esc(v)}" style="flex:1"
          placeholder="${esc(baseVal[0])}" title="内置参考 ${baseVal[0]}-${baseVal[1]}">
        <span style="color:var(--text3);font-size:12px">→</span>
        <input type="time" data-solar="${key}1" value="${esc(ov[key]?ov[key][1]:'')}"
          placeholder="${esc(baseVal[1])}" title="内置参考 ${baseVal[0]}-${baseVal[1]}">
      </div>
      <div class="hint" style="font-size:10.5px">内置：${esc(baseVal[0])}–${esc(baseVal[1])}</div>
    </div>`;
  };
  return `<div class="solarbox">
    <div class="solarbox-h">
      <b>光影时刻（黄金 / 蓝调）</b>
      <span class="tag" style="font-size:10.5px">${esc(halfTxt)} · 广州 ${m} 月</span>
      <span style="font-size:10.5px;color:var(--text3)">
        日出 ${esc(T.sr)} · 日落 ${esc(T.ss)}</span>
      ${Object.keys(ov).length?'<span class="tag tag-warn" style="font-size:10.5px">已手填覆盖</span>':''}
    </div>
    <div class="solarbox-n">
      按<b>太阳高度角</b>算：黄金 +6°~-4°、蓝调 -4°~-6°，与
      <a href="https://miniwebtool.com/zh-cn/%E9%BB%84%E9%87%91%E6%97%B6%E5%88%BB%E5%92%8C%E8%93%9D%E8%B0%83%E6%97%B6%E5%88%BB%E8%AE%A1%E7%AE%97%E5%99%A8/"
         target="_blank" rel="noopener">黄金蓝调计算器</a>同口径。
      <b>换城市请按当地数据手填覆盖</b>（内置表是广州值，纬度差得多时偏差明显）。
    </div>
    <div class="solarbox-g">
      ${f('amG','上午黄金时刻',base.amG,'')}
      ${f('amB','上午蓝调时刻',base.amB,'')}
      ${f('pmG','下午黄金时刻',base.pmG,'')}
      ${f('pmB','下午蓝调时刻',base.pmB,'')}
    </div>
    <div style="display:flex;gap:8px;align-items:center;margin-top:8px">
      <button class="btn sm" data-solar-apply>应用到甘特图</button>
      <button class="btn sm ghost" data-solar-clear>清除手填，回落内置表</button>
      <span style="font-size:10.5px;color:var(--text3)">
        切换 §0.2 的「拍摄时段」会改变甘特图取哪一组</span>
    </div>
  </div>`;
}"""

rep(OLD_SLOTS, NEW_SLOTS)

# ── ② S8_SLOTS 的三处消费点改成 slotSet() ──────────────────────────────
rep("""function slotLinkedSet(){
  return new Set(S8_SLOTS.filter(s=>slotActual(s.k)!=null).map(s=>s.k));
}""",
    """function slotLinkedSet(){
  return new Set(slotSet().filter(s=>slotActual(s.k)!=null).map(s=>s.k));
}""")

rep("""  /* ① 精确名：与 §8.1 关键节点同名 → 用节点配色，保证图例与节点标签一致 */
  const hit=S8_SEG.find(x=>x.k===t);""",
    """  /* ① 精确名：与 §8.1 关键节点同名 → 用节点配色，保证图例与节点标签一致 */
  const hit=slotSet().find(x=>x.k===t);""") if "const hit=S8_SEG.find" in s else None

# segOf 里实际是 S8_SLOTS.find
rep("""  /* ① 精确名：与 §8.1 关键节点同名 → 用节点配色，保证图例与节点标签一致 */
  const hit=S8_SLOTS.find(x=>x.k===t);""",
    """  /* ① 精确名：与 §8.1 关键节点同名 → 用节点配色，保证图例与节点标签一致 */
  const hit=slotSet().find(x=>x.k===t);""")

rep("""  const slots=S8_SLOTS.map(sl=>{""",
    """  const slots=slotSet().map(sl=>{""")

# ── ③ §8.1 加「光影时刻」手填区 + 样式 + 事件委托 ──────────────────────
rep("""  <h3 id="anc-8-1">8.1 拍摄日甘特图<span class="rec" style="color:var(--amber)">可拖拽</span></h3>
  ${gtBlock()}""",
    """  <h3 id="anc-8-1">8.1 拍摄日甘特图<span class="rec" style="color:var(--amber)">可拖拽</span></h3>
  ${solarOvrHtml()}
  ${gtBlock()}""")

# CSS
rep(""".gt-hint{display:flex;align-items:center;gap:9px;flex-wrap:wrap;
  font-size:10.5px;color:var(--text3);padding:6px 2px 0}""",
    """/* v1.0.11：光影时刻（黄金/蓝调）手填覆盖区 */
.solarbox{border:1px solid var(--border);border-left:3px solid #b8863f;
  border-radius:0 var(--r2) var(--r2) 0;background:var(--panel2);
  padding:11px 13px;margin:2px 0 10px}
.solarbox-h{display:flex;align-items:center;gap:9px;flex-wrap:wrap;
  font-size:12.5px;margin-bottom:6px}
.solarbox-h .tag{font-size:10.5px;color:var(--text2);background:var(--panel);
  border:1px solid var(--border);border-radius:20px;padding:1px 8px}
.solarbox-h .tag-warn{color:var(--amber);border-color:var(--amber);background:rgba(184,117,20,.08)}
.solarbox-n{font-size:11px;color:var(--text2);line-height:1.65;margin-bottom:9px}
.solarbox-n a{color:var(--accent)}
.solarbox-g{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}
.solarbox-g .f label{font-size:11.5px}
.solarbox-g .f .hint{margin-top:2px}
@media(max-width:900px){.solarbox-g{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.solarbox-g{grid-template-columns:1fr}}
.gt-hint{display:flex;align-items:center;gap:9px;flex-wrap:wrap;
  font-size:10.5px;color:var(--text3);padding:6px 2px 0}""")

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用 %d 处替换，文件 %d 字符' % (n, len(s)))
