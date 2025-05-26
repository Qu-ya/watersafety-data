#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓中央氣象署 F-D0047-089（未來 7 日市區預報）
輸出 quiz/forecast_weather.json
每 6 小時自動更新（對應 .github/workflows/fetch_forecast.yml）
"""

import os, json, time, requests
from pathlib import Path

# ═════ 1. 基本設定 ═════
API_KEY  = os.environ["CWB_API_KEY"]                          # Codespaces → Secrets
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"
PARAMS   = {"Authorization": API_KEY, "format": "JSON"}
OUT_PATH = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

# 需要抓的 element → 欄位縮寫（新增 WS → wind_speed）
ELEMS = {
    "Wx"      : "weather",      # 天氣現象
    "PoP12h"  : "rain_pct",     # 12h 降雨機率 %
    "MinT"    : "min_temp",     # 最低溫度 °C
    "MaxT"    : "max_temp",     # 最高溫度 °C
    "WS"      : "wind_speed",   # 10 分鐘平均風速 m/s ✅
}

# ═════ 2. 工具函式 ═════
def _safe(obj: dict, key: str, default=""):
    return obj.get(key) or obj.get(key.lower()) or default

def _fetch() -> dict:
    r = requests.get(BASE_URL, params=PARAMS, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("success") != "true":
        raise RuntimeError(f"CWB API failure: {data}")
    return data

def _parse(raw: dict) -> dict:
    recs   = raw["records"]
    locs   = _safe(recs, "locations")[0]                   # 只有一層包全部城市
    cities = _safe(locs, "location", [])

    result = {}
    for city in cities:
        name   = _safe(city, "locationName").strip()
        elems  = _safe(city, "weatherElement", [])

        # 2.1 建立 {elementName → elementObj} 的快速索引
        elem_map = { _safe(e, "elementName"): e for e in elems if _safe(e, "elementName") in ELEMS }

        # 2.2 以 Wx 的 time array 為基準，逐段整併各欄位
        times = _safe(elem_map["Wx"], "time", [])
        blocks = []

        for idx, t in enumerate(times):
            blk = {
                "start" : _safe(t, "startTime")[:16],
                "end"   : _safe(t, "endTime")[:16],
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
    raw = _fetch()
    data = _parse(raw)
    output = {
        "timestamp" : int(time.time()),
        "source"    : "中央氣象署",
        "source_url": BASE_URL,
        "cities"    : data
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ forecast_weather.json 已更新")

if __name__ == "__main__":
    main()
