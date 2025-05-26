#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓中央氣象署 F-D0047-089（22 縣市未來 1 週天氣預報）
輸出 quiz/forecast_weather.json
欄位：天氣現象 Wx、12h 降雨 PoP12h、最低溫 MinT、最高溫 MaxT、風速 WS
"""

import os, json, time, requests, pprint
from pathlib import Path

# ═══ 1. 基本設定 ═══
API_KEY  = os.environ["CWB_API_KEY"]                       # GitHub → Repository secret
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"
PARAMS   = {"Authorization": API_KEY, "format": "JSON"}    # 不加 locationName（089 已是 22 縣市）
OUT_PATH = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

ELEMS = {
    "Wx"     : "weather",
    "PoP12h" : "rain_pct",
    "MinT"   : "min_temp",
    "MaxT"   : "max_temp",
    "WS"     : "wind_speed",
}

# ═══ 2. 共用取值 ═══
def _g(o: dict, k: str, default=""):
    """忽略大小寫取值"""
    return o.get(k) or o.get(k.lower()) or default

# ═══ 3. 下載 ═══
def _fetch() -> dict:
    r = requests.get(BASE_URL, params=PARAMS, timeout=15)
    r.raise_for_status()
    d = r.json()
    if d.get("success") != "true":
        raise RuntimeError(f"CWB API error: {d.get('result', {}).get('message', d)}")
    if not d.get("records"):                                   # 若權限不足會回 ""
        raise RuntimeError("❗ F-D0047-089 尚未授權或流量額度不足，請至 CWA 後台勾選資料集")
    return d

# ═══ 4. 解析 ═══
def _parse(raw: dict) -> dict:
    container = _g(raw["records"], "locations")                # 官方包一層 list
    if isinstance(container, list):
        container = container[0]
    cities = _g(container, "location", [])
    if not cities:
        raise RuntimeError("❗ API 回傳 locations 但無 city 資料")

    res = {}
    for city in cities:
        name   = (_g(city, "locationName") or _g(city, "LocationName")).strip()
        welems = _g(city, "weatherElement", [])
        e_map  = { _g(e, "elementName"): e for e in welems if _g(e, "elementName") in ELEMS }

        times  = _g(e_map["Wx"], "time", [])
        blocks = []
        for i, t in enumerate(times):
            blk = {
                "start": _g(t, "startTime")[:16],
                "end"  : _g(t, "endTime")[:16],
            }
            for en, field in ELEMS.items():
                e_t    = _g(e_map[en], "time", [])
                ev_arr = _g(e_t[i] if i < len(e_t) else {}, "elementValue", [])
                blk[field] = _g(ev_arr[0] if ev_arr else {}, "value")
            blocks.append(blk)
        res[name] = blocks
    return res

# ═══ 5. 主流程 ═══
def main():
    raw  = _fetch()
    data = _parse(raw)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "timestamp" : int(time.time()),
        "source"    : "中央氣象署‧F-D0047-089",
        "source_url": BASE_URL,
        "cities"    : data
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ forecast_weather.json 已更新")

if __name__ == "__main__":
    main()
