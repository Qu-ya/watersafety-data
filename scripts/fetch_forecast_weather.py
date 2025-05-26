#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓中央氣象署 F-D0047-091（臺灣未來 1 週天氣預報）
輸出 quiz/forecast_weather.json
"""

import os, json, time, requests, pprint
from pathlib import Path

# ═════ 1. 基本設定 ═════
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

# ═════ 2. 共用取值 ═════
def _safe(o: dict, k: str, default=""):
    return o.get(k) or o.get(k.lower()) or default

# ═════ 3. 下載 ═════
def _fetch() -> dict:
    r = requests.get(BASE_URL, params=PARAMS, timeout=15)
    r.raise_for_status()
    d = r.json()
    if d.get("success") != "true":
        raise RuntimeError(f"CWB API failure: {d.get('result', {}).get('message', d)}")

    # ← 想觀察原始 JSON 結構可打開下一行
    # pprint.pprint(d, depth=2)

    return d

# ═════ 4. 解析 ═════
def _parse(raw: dict) -> dict:
    recs = raw["records"]

    container = _safe(recs, "locations") or _safe(recs, "location")
    if isinstance(container, list):
        container = container[0]
    if not isinstance(container, dict):
        raise RuntimeError("❗ API 無 locations 物件")

    city_arr = (_safe(container, "location", []) or
                _safe(container, "Location", []))
    if not city_arr:
        raise RuntimeError("❗ API 有 locations 但無 city 資料，請檢查權限")

    result = {}
    for city in city_arr:
        name = (_safe(city, "locationName") or
                _safe(city, "LocationName")).strip()

        elems = _safe(city, "weatherElement", [])
        elem_map = { _safe(e, "elementName"): e
                     for e in elems
                     if _safe(e, "elementName") in ELEMS }

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

# ═════ 5. 主流程 ═════
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
