#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓中央氣象署 F-D0047-089（未來 7 日市區預報）
輸出 quiz/forecast_weather.json
"""

import os, json, time, requests
from pathlib import Path

# ═════ 1. 基本設定 ═════
API_KEY  = os.environ["CWB_API_KEY"]
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"
PARAMS   = {"Authorization": API_KEY, "format": "JSON"}
OUT_PATH = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

ELEMS = {                              # elementName → 欄位縮寫
    "Wx"     : "weather",
    "PoP12h" : "rain_pct",
    "MinT"   : "min_temp",
    "MaxT"   : "max_temp",
    "WS"     : "wind_speed",           # 10分鐘平均風速 m/s
}

# ═════ 2. 工具函式 ═════
def _safe(obj: dict, key: str, default=""):
    """大小寫皆可，若無回傳 default"""
    return obj.get(key) or obj.get(key.lower()) or default

def _fetch() -> dict:
    r = requests.get(BASE_URL, params=PARAMS, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("success") != "true":
        raise RuntimeError(f"CWB API failure: {data}")
    return data

def _parse(raw: dict) -> dict:
    recs = raw["records"]

    # ---- 2.1 取出「裝城市清單」的那層 ----
    # 有些回傳格式是 records.locations (list)，有些直接 records.location (list)
    if "locations" in recs or "Locations" in recs:          # 常見格式
        locs_container = _safe(recs, "locations")[0]        # 只會有一層
        city_arr       = _safe(locs_container, "location", [])
    else:                                                   # 少數 API 版本
        city_arr = _safe(recs, "location", [])

    if not city_arr:
        raise RuntimeError("❗ 無法在 API 回傳中找到任何城市資料")

    # ---- 2.2 組裝每個城市的 12h 區段資料 ----
    result = {}
    for city in city_arr:
        name  = _safe(city, "locationName").strip()
        elems = _safe(city, "weatherElement", [])

        elem_map = { _safe(e, "elementName"): e
                     for e in elems
                     if _safe(e, "elementName") in ELEMS }

        # 以 Wx.time 為基準
        times = _safe(elem_map["Wx"], "time", [])
        blocks = []
        for idx, t in enumerate(times):
            blk = {
                "start": _safe(t, "startTime")[:16],
                "end"  : _safe(t, "endTime")[:16],
            }
            for ename, field in ELEMS.items():
                e = elem_map.get(ename, {})
                t_arr = _safe(e, "time", [])
                v_arr = _safe(t_arr[idx] if idx < len(t_arr) else {}, "elementValue", [])
                blk[field] = _safe(v_arr[0] if v_arr else {}, "value")
            blocks.append(blk)

        result[name] = blocks
    return result

# ═════ 3. 主程式 ═════
def main():
    raw  = _fetch()
    data = _parse(raw)
    output = {
        "timestamp" : int(time.time()),
        "source"    : "中央氣象署",
        "source_url": BASE_URL,
        "cities"    : data
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ forecast_weather.json 已更新")

if __name__ == "__main__":
    main()
