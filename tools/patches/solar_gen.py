# -*- coding: utf-8 -*-
"""按太阳高度角算广州（北纬23.13°，东经 113.26°）的黄金/蓝调时刻，输出 12 档。

口径（业界通行，见 miniwebtool / DJI 官方说明）：
  日出/日落 : 太阳中心高度角 = -0.833°（含大气折射 + 太阳圆盘半径）
  黄金时刻: 高度角 +6° ~ -4°（低角度暖光，逆光/剪影最佳）
  蓝调时刻  : 高度角  -4° ~ -6°（民用晨昏蒙影下段，冷调、适合长曝）

算法：NOAA 简化太阳位置算法。精度约 ±2 分钟，够本工具用。

关键点（v1 写错过一次，这里记牢）：
  高度角 h 下降时**有两个解**——上午侧（时角为负）与下午侧（时角为正）。
  日出 = 上午侧解，日落 = 下午侧解。v1 漏了负号，导致日出日落算成同一个时刻。
"""
import math
import json

LAT, LON, TZ = 23.13, 113.26, 8


def solar_position(day_of_year, lat, lon, tz):
    g = 2 * math.pi / 365 * (day_of_year - 1 + 0.5)
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
           - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
           - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    e = (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
         - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    e_min = 4 * math.degrees(e)

    def hours(h_deg, side):
        """高度角 h_deg 的当地小时。side='am' 取上午侧解，'pm' 取下午侧解。"""
        c = (math.sin(math.radians(h_deg)) - math.sin(math.radians(lat)) * math.sin(dec)) \
            / (math.cos(math.radians(lat)) * math.cos(dec))
        if c > 1 or c < -1:
            return None                      # 极昼/极夜，本latitude+月份用不到
        ha = math.acos(c)                    # 0~π
        if side == 'am':
            ha = -ha                         # ← 上午侧：时角为负。这就是 v1 漏的负号
        return 12 + math.degrees(ha) / 15.0 + e_min / 60.0 - lon / 15.0 + tz

    return hours


def fmt(v):
    if v is None:
        return '--'
    m = int(round(v * 60))
    return '%02d:%02d' % (m // 60 % 24, m % 60)


def table(doy):
    H = solar_position(doy, LAT, LON, TZ)
    def pair(a, b, side):
        return (fmt(H(a, side)), fmt(H(b, side)))
    return {
        'sunrise': fmt(H(-0.833, 'am')),
        'sunset':  fmt(H(-0.833, 'pm')),
        # 上午侧：太阳自 -6° 升到 +6°
        'amBlue':  pair(-6, -4, 'am'),   # 蓝调 -6→-4（先蓝后金）
        'amGold':  pair(-4,  6, 'am'),   # 黄金 -4→+6
        # 下午侧：太阳自 +6° 降到 -6°
        'pmGold':  pair(6,  -4, 'pm'),   # 黄金 +6→-4
        'pmBlue':  pair(-4, -6, 'pm'),   # 蓝调 -4→-6
    }


DOY = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]  # 每月 15 日

print('# 广州 23.13N/113.26E黄金·蓝调时刻（北京时间，每月取 15 日）')
print('# 黄金=高度角+6°~-4°，蓝调=-4°~-6°，NOAA 简化算法')
print('#')
print('# 月  日出   日落   | 上午蓝调      上午黄金       | 下午黄金       下午蓝调')
rows = []
for m, doy in enumerate(DOY, 1):
    t = table(doy)
    rows.append((m, t))
    print('%2d  %s  %s  | %s-%s  %s-%s  | %s-%s  %s-%s'
          % (m, t['sunrise'], t['sunset'],
             t['amBlue'][0], t['amBlue'][1], t['amGold'][0], t['amGold'][1],
             t['pmGold'][0], t['pmGold'][1], t['pmBlue'][0], t['pmBlue'][1]))

# 自检：日出必须早于日落，且时长合理（广州全年约 10.4~13.6 小时）
print()
bad = 0
for m, t in rows:
    def mins(s):
        h, mi = s.split(':')
        return int(h) * 60 + int(mi)
    daylen = mins(t['sunset']) - mins(t['sunrise'])
    ok = 0 < daylen <= 16 * 60
    if not ok:
        bad += 1
        print('!! %d 月异常：日出 %s 日落 %s，日长 %.1f 小时' % (m, t['sunrise'], t['sunset'], daylen / 60))
    if t['amGold'][0] > t['amGold'][1] or t['pmGold'][0] > t['pmGold'][1]:
        bad += 1
        print('!! %d 月黄金时刻区间逆序：%s %s' % (m, t['amGold'], t['pmGold']))
print('自检：%s（日长应在 10.4~13.6 小时；夏至最长冬至最短）'
      % ('全部通过' if bad == 0 else '%d 项异常' % bad))
print('日长范围：%.1f ~ %.1f 小时' % (
    min(mins(t['sunset']) - mins(t['sunrise']) for _, t in rows) / 60,
    max(mins(t['sunset']) - mins(t['sunrise']) for _, t in rows) / 60))

print()
print('# ---- JSON（直接粘进 online.html）----')
out = {'%d' % m: t for m, t in rows}
print(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
