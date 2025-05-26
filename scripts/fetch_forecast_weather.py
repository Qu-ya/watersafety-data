#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓中央氣象署 F-D0047-089（未來 7 日市區預報）
輸出 quiz/forecast_weather.json
"""

import os, json, time, requests
from pathlib import Path

API_KEY  = os.environ["CWB_API_KEY"]
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"
PARAMS   = {"Authorization": API_KEY, "format": "JSON"}
OUT_PATH = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

ELEMS = {
    "Wx"     : "weather",
    "PoP12h" : "rain_pct",
    "MinT"   : "min_temp",
    "MaxT"   : "max_temp",
    "WS"     : "wind_speed",
}

# ---------- 共用安全取值 ----------
def _safe(o: dict, k: str, default=""):
    return o.get(k) or o.get(k.lower()) or default

# ---------- 下載 ----------
def _fetch() -> dict:
    r = requests.get(BASE_URL, params=PARAMS, timeout=15)
    r.raise_for_status()
    d = r.json()

    # 👉 把 debug 放這裡
    import pprint, sys
    pprint.pprint(d, depth=2)
    sys.exit(0)        # 印完立刻結束程式（之後記得移除）
    
    if d.get("success") != "true":
        raise RuntimeError(f"CWB API failure: {d.get('result', {}).get('message', d)}")
    return d

# ---------- 解析 ----------
def _parse(raw: dict) -> dict:
    recs = raw["records"]

    # ① 取出「裝城市清單」那層，可能是 list 也可能是 dict
    container = _safe(recs, "locations") or _safe(recs, "location")
    if isinstance(container, list):
        container = container[0]            # 官方通常包一層 list
    if not isinstance(container, dict):
        raise RuntimeError("❗ API 未回傳合法 locations 欄位，請檢查金鑰與參數")

    city_arr = _safe(container, "location", []) or _safe(container, "Location", [])
    if not city_arr:
        raise RuntimeError("❗ API 雖有 locations，但底下無 city 資料—請檢查大小寫或權限")

    # ② 組裝
    result = {}
    for city in city_arr:
        name  = _safe(city, "locationName") or _safe(city, "LocationName")
        name  = (name or "").strip()
        elems = _safe(city, "weatherElement", [])
        elem_map = { _safe(e, "elementName"): e
                     for e in elems if _safe(e, "elementName") in ELEMS }

        times = _safe(elem_map["Wx"], "time", [])
        blocks = []
        for idx, t in enumerate(times):
            blk = {
                "start": _safe(t, "startTime")[:16],
                "end"  : _safe(t, "endTime")[:16],
            }
            for en, field in ELEMS.items():
                e     = elem_map.get(en, {})
                t_arr = _safe(e, "time", [])
                v_arr = _safe(t_arr[idx] if idx < len(t_arr) else {}, "elementValue", [])
                blk[field] = _safe(v_arr[0] if v_arr else {}, "value")
            blocks.append(blk)
        result[name] = blocks
    return result

# ---------- 主流程 ----------
def main():
    raw  = _fetch()
    data = _parse(raw)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "timestamp" : int(time.time()),
        "source"    : "中央氣象署",
        "source_url": BASE_URL,
        "cities"    : data
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ forecast_weather.json 已更新")

if __name__ == "__main__":
    main()
