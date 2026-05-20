"""
Octopus Agile + Open-Meteo 天气页面生成器  (Kindle Paperwhite 优化版)
======================================================================
目标设备: Kindle Paperwhite 11/12代  (1236-1264px 原生宽度, 300 PPI)
页面策略: max-width 1200px, 22px 基础字号, 纯 SVG 线条图标, 无彩色背景

依赖:  pip install requests python-dotenv
用法:  python generate.py
"""

import os, math, requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# ── Octopus 配置 ──────────────────────────────────────────────────────────────
PRODUCT_CODE        = os.getenv("OCTOPUS_PRODUCT_CODE") or "AGILE-24-10-01"
TARIFF_CODE         = os.getenv("OCTOPUS_TARIFF_CODE")  or "E-1R-AGILE-24-10-01-C"
BASE_URL            = os.getenv("OCTOPUS_BASE_URL",      "https://api.octopus.energy/v1")
TARIFF_DISPLAY_NAME = "Agile Octopus October 2024 v1"
TARIFF_REGION       = "London C"
RATE_GREEN          = 20.0
RATE_YELLOW         = 25.0

# ── 天气配置 ──────────────────────────────────────────────────────────────────
WEATHER_LAT  = 51.4123
WEATHER_LON  = -0.3007
WEATHER_CITY = "Kingston upon Thames"

# ── 家电时长 (半小时时段数) ────────────────────────────────────────────────────
WASH_SLOTS = 7   # 3.5 小时
DRY_SLOTS  = 7   # 3.5 小时


# ════════════════════════════════════════════════════════════════════════════
#  SVG 图标 (纯线条, 墨水屏友好)
# ════════════════════════════════════════════════════════════════════════════

def _svg(content, size=40, stroke=3.0, viewbox="0 0 24 24"):
    return (f'<svg width="{size}" height="{size}" viewBox="{viewbox}" '
            f'fill="none" stroke="black" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round">{content}</svg>')

# 天气图标
def svg_sun(size=40):
    return _svg('<circle cx="12" cy="12" r="4"/>'
                '<line x1="12" y1="1.5" x2="12" y2="4.5"/>'
                '<line x1="12" y1="19.5" x2="12" y2="22.5"/>'
                '<line x1="1.5" y1="12" x2="4.5" y2="12"/>'
                '<line x1="19.5" y1="12" x2="22.5" y2="12"/>'
                '<line x1="4.6" y1="4.6" x2="6.7" y2="6.7"/>'
                '<line x1="17.3" y1="17.3" x2="19.4" y2="19.4"/>'
                '<line x1="19.4" y1="4.6" x2="17.3" y2="6.7"/>'
                '<line x1="6.7" y1="17.3" x2="4.6" y2="19.4"/>', size)

def svg_moon(size=40):
    return _svg('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>', size)

def svg_cloud(size=40):
    return _svg('<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z"/>', size)

def svg_sun_cloud(size=40):
    return _svg('<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41'
                'M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'
                '<circle cx="12" cy="10" r="3"/>'
                '<path d="M15 17H7.5a3.5 3.5 0 0 1 0-7h.14A3.5 3.5 0 0 1 15 13"/>'
                '<path d="M15 13h1.5a3 3 0 0 1 0 6H15"/>', size, stroke=1.6)

def svg_cloud_rain(size=40):
    return _svg('<path d="M16 13v8M8 13v8M12 15v8"/>'
                '<path d="M17.5 8H9a5 5 0 0 1 8.5-3.5A4.5 4.5 0 1 1 17.5 8z"/>', size)

def svg_cloud_drizzle(size=40):
    return _svg('<path d="M8 19v1M8 13v3M16 19v1M16 13v3M12 21v1M12 13v5"/>'
                '<path d="M17.5 8H9a5 5 0 0 1 8.5-3.5A4.5 4.5 0 1 1 17.5 8z"/>', size)

def svg_cloud_snow(size=40):
    return _svg('<path d="M20 17.58A5 5 0 0 0 18 8h-1.26A8 8 0 1 0 4 16.25"/>'
                '<line x1="8" y1="16" x2="8.01" y2="16"/>'
                '<line x1="8" y1="20" x2="8.01" y2="20"/>'
                '<line x1="12" y1="18" x2="12.01" y2="18"/>'
                '<line x1="12" y1="22" x2="12.01" y2="22"/>'
                '<line x1="16" y1="16" x2="16.01" y2="16"/>'
                '<line x1="16" y1="20" x2="16.01" y2="20"/>', size)

def svg_storm(size=40):
    return _svg('<path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/>'
                '<polyline points="13 11 9 17 15 17 11 23"/>', size)

def svg_fog(size=40):
    return _svg('<line x1="3" y1="8" x2="21" y2="8"/>'
                '<line x1="3" y1="12" x2="21" y2="12"/>'
                '<line x1="3" y1="16" x2="21" y2="16"/>'
                '<line x1="6" y1="4" x2="18" y2="4"/>'
                '<line x1="6" y1="20" x2="18" y2="20"/>', size)

def svg_overcast(size=40):
    return _svg('<path d="M17.5 21H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z"/>'
                '<path d="M20 16H6" stroke-dasharray="2 2" stroke-width="1"/>', size)

# 电力/家电图标
def svg_bolt(size=36):
    return _svg('<polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>', size)

def svg_star(size=36):
    return _svg('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 '
                '12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>', size)

def svg_washer(size=36):
    # 前置洗衣机: 外框 + 圆窗 + 小按钮
    return _svg('<rect x="2" y="2" width="20" height="20" rx="2"/>'
                '<circle cx="12" cy="13" r="5"/>'
                '<circle cx="12" cy="13" r="2.5"/>'
                '<circle cx="6.5" cy="5.5" r="0.8" fill="black"/>'
                '<circle cx="9.5" cy="5.5" r="0.8" fill="black"/>'
                '<line x1="13" y1="5.5" x2="17" y2="5.5"/>', size)

def svg_dryer(size=36):
    # 烘干机: 外框 + 圆门 + 热量线
    return _svg('<rect x="2" y="2" width="20" height="20" rx="2"/>'
                '<circle cx="12" cy="13" r="5"/>'
                '<path d="M9.5 11 Q12 9 14.5 11" stroke-width="1.5"/>'
                '<path d="M9.5 13 Q12 11 14.5 13" stroke-width="1.5"/>'
                '<path d="M9.5 15 Q12 13 14.5 15" stroke-width="1.5"/>'
                '<circle cx="6.5" cy="5.5" r="0.8" fill="black"/>'
                '<line x1="11" y1="5.5" x2="17" y2="5.5"/>', size)

def svg_plug(size=36):
    return _svg('<path d="M5 13H3a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1h2"/>'
                '<path d="M19 13h2a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1h-2"/>'
                '<rect x="5" y="5" width="14" height="8" rx="2"/>'
                '<path d="M9 21v-4"/><path d="M15 21v-4"/>'
                '<path d="M9 17h6"/>', size)

def svg_clock(size=32):
    return _svg('<circle cx="12" cy="12" r="10"/>'
                '<polyline points="12 6 12 12 16 14"/>', size)

# EV car (best charging)
def svg_car(size=36):
    return _svg(
        '<path d="M2 15h20v4H2z"/>'          # body
        '<path d="M5 15l3-6h8l3 6"/>'        # cabin
        '<circle cx="7" cy="19" r="2"/>'     # rear wheel
        '<circle cx="17" cy="19" r="2"/>'    # front wheel
        '<line x1="4" y1="17" x2="2" y2="17"/>'
        '<line x1="20" y1="17" x2="22" y2="17"/>',
        size)

# Location pin
def svg_pin_sm(size=20):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="black" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" '
            f'style="vertical-align:middle;margin-right:4px">'
            f'<path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/>'
            f'<circle cx="12" cy="10" r="3"/>'
            f'</svg>')

# Small inline icons (for weather cards & header)
def _svg_sm(content, size=20, stroke=2.4):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="black" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="vertical-align:middle;margin-right:2px">{content}</svg>')

def svg_drop_sm(size=20):
    """Water drop — humidity"""
    return _svg_sm('<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>', size)

def svg_rain_sm(size=20):
    """Cloud + rain lines — precipitation probability"""
    return _svg_sm(
        '<path d="M17 12H9a5 5 0 0 1 8-4A4 4 0 1 1 17 12z"/>'
        '<line x1="8" y1="15" x2="7" y2="19"/>'
        '<line x1="12" y1="15" x2="11" y2="19"/>'
        '<line x1="16" y1="15" x2="15" y2="19"/>',
        size)

def svg_wind_arrow(degrees, size=22):
    """Directional arrow showing where wind blows TO"""
    go = (degrees + 180) % 360
    rad = math.radians(go)
    dx, dy = math.sin(rad), -math.cos(rad)
    cx, cy = 12, 12
    tx, ty   = cx + 6.5*dx, cy + 6.5*dy   # tip
    bx, by   = cx - 5.5*dx, cy - 5.5*dy   # tail
    pr = rad + math.pi/2
    w  = 2.3
    a1x, a1y = tx - 3.5*dx + w*math.sin(pr), ty - 3.5*dy - w*math.cos(pr)
    a2x, a2y = tx - 3.5*dx - w*math.sin(pr), ty - 3.5*dy + w*math.cos(pr)
    content = (
        f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tx:.1f}" y2="{ty:.1f}"/>'
        f'<line x1="{a1x:.1f}" y1="{a1y:.1f}" x2="{tx:.1f}" y2="{ty:.1f}"/>'
        f'<line x1="{a2x:.1f}" y1="{a2y:.1f}" x2="{tx:.1f}" y2="{ty:.1f}"/>'
    )
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="black" stroke-width="2.8" stroke-linecap="round" '
            f'style="vertical-align:middle;margin-right:2px">{content}</svg>')

# WMO 代码 → SVG
def weather_svg(code: int, is_day: int = 1, size: int = 44) -> str:
    if   code == 0:                return svg_sun(size) if is_day else svg_moon(size)
    elif code == 1:                return svg_sun_cloud(size) if is_day else svg_moon(size)
    elif code == 2:                return svg_sun_cloud(size)
    elif code == 3:                return svg_overcast(size)
    elif code in (45, 48):         return svg_fog(size)
    elif code in (51, 53, 55):     return svg_cloud_drizzle(size)
    elif code in (61, 63, 65):     return svg_cloud_rain(size)
    elif code in (71, 73, 75, 77): return svg_cloud_snow(size)
    elif code in (80, 81, 82):     return svg_cloud_rain(size)
    elif code in (85, 86):         return svg_cloud_snow(size)
    elif code in (95, 96, 99):     return svg_storm(size)
    else:                          return svg_cloud(size)

def wind_label(deg: float) -> str:
    dirs   = ["N","NE","E","SE","S","SW","W","NW"]
    arrows = ["↓","↙","←","↖","↑","↗","→","↘"]
    idx = round(deg / 45) % 8
    return f"{dirs[idx]}{arrows[idx]}"


# ════════════════════════════════════════════════════════════════════════════
#  API
# ════════════════════════════════════════════════════════════════════════════

def fetch_weather() -> dict:
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": WEATHER_LAT, "longitude": WEATHER_LON,
        "hourly":  ("temperature_2m,relative_humidity_2m,precipitation_probability,"
                    "wind_speed_10m,wind_direction_10m,weathercode,is_day"),
        "current": ("temperature_2m,relative_humidity_2m,wind_speed_10m,"
                    "wind_direction_10m,weathercode,is_day"),
        "timezone": "Europe/London", "forecast_days": 2, "wind_speed_unit": "mph",
    }, timeout=15)
    r.raise_for_status(); return r.json()

def fetch_rates(period_from, period_to) -> list:
    r = requests.get(
        f"{BASE_URL}/products/{PRODUCT_CODE}/electricity-tariffs/{TARIFF_CODE}/standard-unit-rates/",
        params={"period_from": period_from, "period_to": period_to, "page_size": 100},
        timeout=15)
    r.raise_for_status()
    res = r.json().get("results", [])
    res.sort(key=lambda x: x["valid_from"]); return res

def get_next_hours(wd: dict, n=5) -> list:
    h = wd["hourly"]; times = h["time"]
    now_bst = datetime.now(timezone.utc) + timedelta(hours=1)
    floor   = now_bst.replace(tzinfo=None, minute=0, second=0, microsecond=0)
    out = []
    for i, t in enumerate(times):
        if datetime.fromisoformat(t) >= floor:
            for j in range(n):
                k = i + j
                if k < len(times):
                    out.append({
                        "time":   datetime.fromisoformat(times[k]).strftime("%H:%M"),
                        "temp":   h["temperature_2m"][k],
                        "hum":    h["relative_humidity_2m"][k],
                        "precip": h["precipitation_probability"][k],
                        "wind":   h["wind_speed_10m"][k],
                        "wdir":   h["wind_direction_10m"][k],
                        "code":   h["weathercode"][k],
                        "is_day": h["is_day"][k],
                    })
            break
    return out


# ════════════════════════════════════════════════════════════════════════════
#  电价分析
# ════════════════════════════════════════════════════════════════════════════

def rate_class(p):
    return "green" if p < RATE_GREEN else ("yellow" if p < RATE_YELLOW else "red")

def fmt_bst(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (dt + timedelta(hours=1)).strftime("%H:%M")

def fmt_dur(slots):
    h = slots * 0.5
    return f"{h:.0f}h" if h == int(h) else f"{h:.1f}h"

def find_cheap_windows(slots, threshold=RATE_GREEN, min_slots=4):
    wins, i = [], 0
    while i < len(slots):
        if slots[i]["value_inc_vat"] < threshold:
            j = i
            while j < len(slots) and slots[j]["value_inc_vat"] < threshold: j += 1
            if j - i >= min_slots:
                blk = slots[i:j]
                avg = sum(s["value_inc_vat"] for s in blk) / len(blk)
                wins.append({"start": blk[0]["valid_from"], "end": blk[-1]["valid_to"],
                             "count": len(blk), "avg": avg,
                             "min": min(s["value_inc_vat"] for s in blk)})
            i = j
        else: i += 1
    return wins

def find_appliance_plan(slots):
    total = WASH_SLOTS + DRY_SLOTS
    best_avg, best = float("inf"), None
    for i in range(len(slots) - total + 1):
        blk = slots[i:i+total]
        if sum(1 for s in blk if s["value_inc_vat"] >= RATE_YELLOW) > 4: continue
        avg = sum(s["value_inc_vat"] for s in blk) / total
        if avg < best_avg:
            best_avg = avg
            w, d = blk[:WASH_SLOTS], blk[WASH_SLOTS:]
            best = {"mode": "combined",
                    "wash_start": w[0]["valid_from"], "wash_end": w[-1]["valid_to"],
                    "wash_avg": sum(s["value_inc_vat"] for s in w)/WASH_SLOTS,
                    "dry_start": d[0]["valid_from"],  "dry_end": d[-1]["valid_to"],
                    "dry_avg":  sum(s["value_inc_vat"] for s in d)/DRY_SLOTS,
                    "total_avg": avg}
    if best: return best
    def cheapest(n):
        ba, bb = float("inf"), None
        for i in range(len(slots)-n+1):
            blk = slots[i:i+n]; avg = sum(s["value_inc_vat"] for s in blk)/n
            if avg < ba: ba, bb = avg, blk
        return bb
    w = cheapest(WASH_SLOTS); d = cheapest(DRY_SLOTS)
    if w and d:
        return {"mode": "separate",
                "wash_start": w[0]["valid_from"], "wash_end": w[-1]["valid_to"],
                "wash_avg": sum(s["value_inc_vat"] for s in w)/WASH_SLOTS,
                "dry_start": d[0]["valid_from"],  "dry_end": d[-1]["valid_to"],
                "dry_avg":  sum(s["value_inc_vat"] for s in d)/DRY_SLOTS}
    return None


# ════════════════════════════════════════════════════════════════════════════
#  费率曲线 SVG
# ════════════════════════════════════════════════════════════════════════════

def build_rate_svg(slots, now_utc, width=1160, height=130):
    bst_now   = now_utc + timedelta(hours=1)
    show_next = bst_now.hour >= 17

    # 决定显示哪些时段 — 始终从当前时间前 2 小时开始
    start_cutoff = now_utc - timedelta(hours=2)
    if show_next:
        # 当日剩余 + 明日: 从 now-2h 起, 最多 60 槽 (30 小时)
        disp = [s for s in slots
                if datetime.fromisoformat(s["valid_from"].replace("Z","+00:00")) >= start_cutoff]
        disp = disp[:60]
    else:
        # 当日 now-2h 到 23:59 BST
        day_start = bst_now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        day_end   = day_start + timedelta(days=1)
        disp = [s for s in slots
                if (datetime.fromisoformat(s["valid_from"].replace("Z","+00:00")) >= start_cutoff
                    and (datetime.fromisoformat(s["valid_from"].replace("Z","+00:00"))
                         + timedelta(hours=1)).replace(tzinfo=None) < day_end)]

    if len(disp) < 2: return ""

    rates  = [s["value_inc_vat"] for s in disp]
    n      = len(disp)
    lo     = max(0, min(rates) - 3)
    hi     = max(rates) + 4

    pad_l, pad_r, pad_t, pad_b = 44, 10, 12, 28
    cw = width  - pad_l - pad_r
    ch = height - pad_t - pad_b

    def px(i):    return pad_l + (i / (n - 1)) * cw
    def py(rate): return pad_t + (1 - (rate - lo) / (hi - lo)) * ch

    pts = [(px(i), py(r)) for i, r in enumerate(rates)]
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    # Fill area (closed path)
    fill_path = (f"M{pts[0][0]:.1f},{py(lo):.1f} "
                 + " ".join(f"L{x:.1f},{y:.1f}" for x, y in pts)
                 + f" L{pts[-1][0]:.1f},{py(lo):.1f} Z")

    # Threshold lines
    gy = py(RATE_GREEN);  gy_ok = pad_t <= gy <= pad_t + ch
    yy = py(RATE_YELLOW); yy_ok = pad_t <= yy <= pad_t + ch

    # Current slot marker
    cur_x = cur_y = cur_rate = None
    for i, s in enumerate(disp):
        sf = datetime.fromisoformat(s["valid_from"].replace("Z","+00:00"))
        st = datetime.fromisoformat(s["valid_to"].replace("Z","+00:00"))
        if sf <= now_utc < st:
            cur_x, cur_y, cur_rate = px(i), py(s["value_inc_vat"]), s["value_inc_vat"]
            break

    # X-axis time labels (every 3 hours = 6 slots)
    time_labels = []
    for i, s in enumerate(disp):
        bst_t = (datetime.fromisoformat(s["valid_from"].replace("Z","+00:00"))
                 + timedelta(hours=1))
        if bst_t.minute == 0 and bst_t.hour % 3 == 0:
            time_labels.append((px(i), bst_t.strftime("%H")))

    # Y-axis labels (every 10p)
    y_labels = []
    for p in range(int(lo), int(hi)+1):
        if p % 10 == 0:
            yp = py(p)
            if pad_t <= yp <= pad_t + ch:
                y_labels.append((yp, f"{p}"))

    svg = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
           f'xmlns="http://www.w3.org/2000/svg" style="display:block">']

    # Fill
    svg.append(f'<path d="{fill_path}" fill="#e8e8e8" stroke="none"/>')

    # Threshold lines
    if gy_ok:
        svg.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{pad_l+cw}" y2="{gy:.1f}" '
                   f'stroke="#555" stroke-width="0.8" stroke-dasharray="4 3"/>')
        svg.append(f'<text x="{pad_l-3}" y="{gy+4:.1f}" text-anchor="end" '
                   f'font-size="20" fill="#222">{RATE_GREEN:.0f}</text>')
    if yy_ok:
        svg.append(f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{pad_l+cw}" y2="{yy:.1f}" '
                   f'stroke="#888" stroke-width="0.8" stroke-dasharray="2 3"/>')

    # Main polyline
    svg.append(f'<polyline points="{polyline}" fill="none" stroke="black" stroke-width="2.5"/>')

    # Y-axis labels
    for yp, label in y_labels:
        svg.append(f'<text x="{pad_l-4}" y="{yp+4:.1f}" text-anchor="end" '
                   f'font-size="20" fill="#333">{label}p</text>')

    # X-axis time labels
    for xp, label in time_labels:
        svg.append(f'<text x="{xp:.1f}" y="{pad_t+ch+20:.1f}" text-anchor="middle" '
                   f'font-size="22" fill="#222">{label}:00</text>')

    # Axes
    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t+ch}" '
               f'stroke="#aaa" stroke-width="1"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t+ch:.1f}" x2="{pad_l+cw}" y2="{pad_t+ch:.1f}" '
               f'stroke="#aaa" stroke-width="1"/>')

    # Current marker
    if cur_x is not None:
        svg.append(f'<line x1="{cur_x:.1f}" y1="{pad_t}" x2="{cur_x:.1f}" y2="{pad_t+ch}" '
                   f'stroke="black" stroke-width="2.0" stroke-dasharray="5 3"/>')
        svg.append(f'<circle cx="{cur_x:.1f}" cy="{cur_y:.1f}" r="7" fill="black"/>')
        # Rate label near dot
        lx = min(cur_x + 10, pad_l + cw - 60)
        svg.append(f'<text x="{lx:.1f}" y="{cur_y-10:.1f}" font-size="26" '
                   f'font-weight="bold" fill="black">{cur_rate:.1f}p</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ════════════════════════════════════════════════════════════════════════════
#  CSS  (Kindle Paperwhite 原生像素优化, 22px 基础字号)
# ════════════════════════════════════════════════════════════════════════════

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 32px;
    font-weight: 500;
    line-height: 1.35;
    background: #fff;
    color: #000;
    max-width: 1240px;
    margin: 0 auto;
    padding: 10px 16px 20px;
}

/* ── Weather section ────────────────────────────────────── */
.wx-wrap {
    border: 2.5px solid #000;
    border-radius: 12px;
    padding: 16px 18px 14px;
    margin-bottom: 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.wx-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 10px;
    border-bottom: 2px solid #888;
    margin-bottom: 10px;
}
.wx-left  { display: flex; flex-direction: column; gap: 4px; }
.wx-city  { font-size: 1.05em; font-weight: 700; letter-spacing: 0.02em; }
.wx-meta  { font-size: 0.82em; color: #111; font-weight: 500; }
.wx-right { text-align: right; }
.wx-temp-big { font-size: 2.4em; font-weight: 600; line-height: 1; }
.wx-time  { font-size: 0.72em; color: #333; margin-top: 2px; font-weight: 500; }

/* 3-card row — float layout for max browser compatibility */
.wx-cards { overflow: hidden; }
.wx-cards::after { content: ""; display: table; clear: both; }
.wx-card {
    float: left;
    width: 32%;
    box-sizing: border-box;
    border: 2px solid #888;
    border-radius: 10px;
    text-align: center;
    padding: 10px 4px 8px;
}
.wx-card:nth-child(2) { margin-left: 2%; margin-right: 2%; }
.wx-card.now { border: 3px solid #000; background: #ececec; }
.wc-time { font-size: 0.78em; color: #111; margin-bottom: 4px; font-weight: 700; }
.wc-icon { display: flex; justify-content: center; margin-bottom: 4px; }
.wc-temp { font-size: 1.2em; font-weight: 700; margin-bottom: 5px; }
.wc-hum  { font-size: 0.76em; color: #111; margin-bottom: 3px; font-weight: 500; }
.wc-rain { font-size: 0.76em; color: #000; margin-bottom: 3px; font-weight: 600; }
.wc-wind { font-size: 0.76em; color: #111; line-height: 1.5; font-weight: 500; }

/* ── Rate curve ─────────────────────────────────────────── */
.rate-curve-wrap {
    border: 2px solid #888;
    border-radius: 10px;
    padding: 12px 16px 8px;
    margin-bottom: 12px;
}
.rate-curve-title {
    font-size: 0.72em;
    color: #333;
    font-weight: 600;
    margin-bottom: 6px;
}

/* ── Appliance boxes — float layout ─────────────────────── */
.appliance-boxes { overflow: hidden; margin-bottom: 14px; }
.appliance-boxes::after { content: ""; display: table; clear: both; }
.ap-box {
    float: left;
    width: 32%;
    box-sizing: border-box;
    border: 2.5px solid #000;
    border-radius: 10px;
    padding: 14px 6px 12px;
    text-align: center;
}
.ap-box:nth-child(2) { margin-left: 2%; margin-right: 2%; }
.ap-box.alt { background: #f0f0f0; }
.ap-icon  { margin-bottom: 4px; }
.ap-title { font-weight: 700; font-size: 0.9em; margin-bottom: 4px; }
.ap-detail { font-size: 0.86em; font-weight: 600; line-height: 1.55; color: #000; word-break: break-word; }

/* ── Rate table ──────────────────────────────────────────── */
.rates-wrap { margin-top: 12px; }
.rates-title {
    font-size: 0.72em; color: #333; font-weight: 600;
    border-bottom: 2px solid #000;
    padding-bottom: 5px; margin-bottom: 4px;
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;
}
.legend span { margin-right: 12px; }
table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
th { padding: 5px 10px; border-bottom: 2.5px solid #000; text-align: left; font-weight: 700; }
td { padding: 4px 10px; border-bottom: 1.5px solid #ccc; }
tr.cur td { font-weight: 700; background: #d8d8d8 !important; border-left: 5px solid #000; }
tr.green  { background: #fff; }
tr.yellow { background: #f0f0f0; }
tr.red    { background: #e4e4e4; color: #222; font-weight: 600; }
td .tag   { font-size: 0.8em; margin-right: 5px; font-weight: 700; }

/* ── Footer ────────────────────────────────────────────── */
.footer {
    font-size: 0.65em; color: #555; font-weight: 500; text-align: center;
    margin-top: 12px; padding-top: 6px; border-top: 1.5px solid #ccc;
}
"""


# ════════════════════════════════════════════════════════════════════════════
#  HTML 组装
# ════════════════════════════════════════════════════════════════════════════

def build_html(slots, weather_data, generated_at):
    now_utc = datetime.now(timezone.utc)
    bst_now = now_utc + timedelta(hours=1)
    bst_str = bst_now.strftime("%H:%M BST  ·  %a %d %b %Y")

    # ── 天气 ──────────────────────────────────────────────────────────────
    cw       = weather_data.get("current", {})
    cur_temp = cw.get("temperature_2m", 0)
    cur_hum  = cw.get("relative_humidity_2m", 0)
    cur_wind = cw.get("wind_speed_10m", 0)
    cur_wdir = cw.get("wind_direction_10m", 0)
    cur_icon_svg = weather_svg(cw.get("weathercode", 0), cw.get("is_day", 1), size=44)

    hours = get_next_hours(weather_data, 3)
    cards_html = ""
    for idx, h in enumerate(hours):
        cls  = "wx-card now" if idx == 0 else "wx-card"
        lbl  = "Now" if idx == 0 else h["time"]
        icon = weather_svg(h["code"], h["is_day"], size=54)
        rain = (f'<div class="wc-rain">{svg_rain_sm(26)} {h["precip"]}%</div>'
                if h["precip"] >= 10 else "")
        cards_html += f"""
    <div class="{cls}">
      <div class="wc-time">{lbl}</div>
      <div class="wc-icon">{icon}</div>
      <div class="wc-temp">{h['temp']:.0f}°C</div>
      <div class="wc-hum">{svg_drop_sm(26)} {h['hum']:.0f}%</div>
      {rain}
      <div class="wc-wind">{svg_wind_arrow(h['wdir'], 28)} {wind_label(h['wdir'])} {h['wind']:.0f}mph</div>
    </div>"""

    # ── 当前时段 (仅用于费率表高亮) ───────────────────────────────────────
    current_slot = None
    for s in slots:
        sf = datetime.fromisoformat(s["valid_from"].replace("Z","+00:00"))
        st = datetime.fromisoformat(s["valid_to"].replace("Z","+00:00"))
        if sf <= now_utc < st: current_slot = s; break

    # ── 费率曲线 ───────────────────────────────────────────────────────────
    curve_svg = build_rate_svg(slots, now_utc)
    curve_label = ("Remaining today + tomorrow's rates" if bst_now.hour >= 17
                   else "Today's 24-hour rate curve")
    curve_html = f"""
<div class="rate-curve-wrap">
  <div class="rate-curve-title">{curve_label}</div>
  {curve_svg}
</div>"""

    # ── 家电三格 (EV / Washer / Dryer) ────────────────────────────────────
    windows = find_cheap_windows(slots)
    plan    = find_appliance_plan(slots)

    ev_box = ""
    if windows:
        bw    = min(windows, key=lambda x: x["avg"])
        miles = bw["count"] * 7.5
        ev_box = f"""
  <div class="ap-box">
    <span class="ap-icon">{svg_car(40)}</span>
    <div class="ap-title">EV</div>
    <div class="ap-detail">{fmt_bst(bw['start'])} → {fmt_bst(bw['end'])}<br>avg {bw['avg']:.1f}p &nbsp;·&nbsp; ≈{miles:.0f} mi</div>
  </div>"""

    wash_box = dry_box = ""
    if plan:
        wash_box = f"""
  <div class="ap-box">
    <span class="ap-icon">{svg_washer(40)}</span>
    <div class="ap-title">Washer</div>
    <div class="ap-detail">{fmt_bst(plan['wash_start'])} → {fmt_bst(plan['wash_end'])}<br>avg {plan['wash_avg']:.1f}p &nbsp;·&nbsp; {fmt_dur(WASH_SLOTS)}</div>
  </div>"""
        dry_box = f"""
  <div class="ap-box alt">
    <span class="ap-icon">{svg_dryer(40)}</span>
    <div class="ap-title">Dryer</div>
    <div class="ap-detail">{fmt_bst(plan['dry_start'])} → {fmt_bst(plan['dry_end'])}<br>avg {plan['dry_avg']:.1f}p &nbsp;·&nbsp; {fmt_dur(DRY_SLOTS)}</div>
  </div>"""

    appliance_boxes_html = (f'<div class="appliance-boxes">{ev_box}{wash_box}{dry_box}\n</div>'
                            if (ev_box or wash_box) else "")

    # ── 费率表：从当前时段开始显示 ────────────────────────────────────────────
    cur_idx = 0
    if current_slot:
        for i, s in enumerate(slots):
            if s["valid_from"] == current_slot["valid_from"]:
                cur_idx = i; break
    ordered = slots[cur_idx:] + slots[:cur_idx]

    rows = ""
    for s in ordered:
        p  = s["value_inc_vat"]; rc = rate_class(p)
        is_cur = current_slot and s["valid_from"] == current_slot["valid_from"]
        tags = ""
        if plan:
            if plan["wash_start"] <= s["valid_from"] < plan["wash_end"]:
                tags += '<span class="tag">W</span>'
            if plan["dry_start"]  <= s["valid_from"] < plan["dry_end"]:
                tags += '<span class="tag">D</span>'
        row_cls = ("cur " if is_cur else "") + rc
        rows += (f'<tr class="{row_cls}"><td>{tags}{fmt_bst(s["valid_from"])}–'
                 f'{fmt_bst(s["valid_to"])}</td><td>{p:.2f}p</td></tr>\n')

    gen_time = generated_at.strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agile + Weather</title>
<style>{CSS}</style>
</head>
<body>

<!-- Weather -->
<div class="wx-wrap">
  <div class="wx-top">
    <div class="wx-left">
      <span class="wx-city">{svg_pin_sm(28)} {WEATHER_CITY}</span>
      <span class="wx-meta">{svg_drop_sm(26)} {cur_hum:.0f}% &nbsp;&nbsp; {svg_wind_arrow(cur_wdir, 28)} {wind_label(cur_wdir)} {cur_wind:.0f} mph</span>
    </div>
    <div class="wx-right">
      <div class="wx-temp-big">{cur_temp:.0f}° {cur_icon_svg}</div>
      <div class="wx-time">{bst_str}</div>
    </div>
  </div>
  <div class="wx-cards">{cards_html}</div>
</div>

<!-- Rate curve -->
{curve_html}

<!-- Appliance boxes: EV / Washer / Dryer -->
{appliance_boxes_html}

<!-- Rate table -->
<div class="rates-wrap">
  <div class="rates-title">
    <span>{TARIFF_DISPLAY_NAME} · {TARIFF_REGION}</span>
    <span class="legend">
      <span>✓ &lt;{RATE_GREEN:.0f}p</span>
      <span>~ {RATE_GREEN:.0f}–{RATE_YELLOW:.0f}p</span>
      <span>✗ &gt;{RATE_YELLOW:.0f}p</span>
      <span>W=Washer D=Dryer</span>
    </span>
  </div>
  <table>
    <thead><tr><th>Slot (BST)</th><th>Rate (inc. VAT)</th></tr></thead>
    <tbody>
{rows}    </tbody>
  </table>
</div>

<p class="footer">Generated: {gen_time} &nbsp;|&nbsp; Auto-updated every 4h &nbsp;|&nbsp; Page refreshes at :00 &amp; :30</p>

<script>
// Refresh at the next exact :00 or :30 minute mark
(function scheduleRefresh() {{
  var now = new Date();
  var min = now.getMinutes(), sec = now.getSeconds(), ms = now.getMilliseconds();
  var minsLeft = min < 30 ? (30 - min) : (60 - min);
  var msLeft = minsLeft * 60000 - sec * 1000 - ms + 800;
  setTimeout(function() {{ location.reload(); }}, msLeft);
}})();
</script>
</body>
</html>"""


# ════════════════════════════════════════════════════════════════════════════
#  入口
# ════════════════════════════════════════════════════════════════════════════

def main():
    now_utc = datetime.now(timezone.utc)
    t0 = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    t1 = t0 + timedelta(days=2)
    print("📡 获取 Agile 费率…")
    slots = fetch_rates(t0.strftime("%Y-%m-%dT%H:%M:%SZ"), t1.strftime("%Y-%m-%dT%H:%M:%SZ"))
    print(f"   → {len(slots)} 个时段")
    print(f"🌤  获取 {WEATHER_CITY} 天气…")
    wd = fetch_weather()
    print(f"   → {wd['current']['temperature_2m']}°C  code={wd['current']['weathercode']}")
    html = build_html(slots, wd, generated_at=now_utc)
    out  = os.path.join(os.path.dirname(__file__), "index.html")
    with open(out, "w", encoding="utf-8") as f: f.write(html)
    print(f"📄 index.html 已生成 ({len(html):,} 字节) → {out}")

if __name__ == "__main__":
    main()
