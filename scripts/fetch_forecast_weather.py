#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中央氣象署 F-D0047-089（22 縣市未來 1 週預報）
輸出 quiz/forecast_weather.json
"""

import os, json, time, requests
from pathlib import Path

# ===== 1. 基本設定 =====
API_KEY  = os.environ["CWB_API_KEY"]
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"
PARAMS   = {"Authorization": API_KEY, "format": "JSON"}
OUT_PATH = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

ELEMS = {
    "Wx"     : "weather",
    "PoP12h" : "rain_pct",
    "MinT"   : "min_temp",
    "MaxT"   : "max_temp",
    "WS"     : "wind_speed",
}

def _g(o: dict, k: str, default=""):
    """忽略大小寫取值"""
    return o.get(k) or o.get(k.lower()) or default

# ===== 2. 下載 =====
def _fetch() -> dict:
    r = requests.get(BASE_URL, params=PARAMS, timeout=15)
    r.raise_for_status()
    d = r.json()

    # success 但 records 是 "" ＝ 沒授權或流量超限
    if not d.get("records"):
        #err = d.get("result", {}).get("message", "records 是空字串")
        # ★ 把官方訊息印出，再丟錯
        msg = d.get("result", {}).get("message", "records 空字串")
        raise RuntimeError(f"❗ CWA 回傳空資料：{err}\n請到後台勾選 F-D0047-089 或檢查流量額度")
    return d

# ===== 3. 解析 =====
def _parse(raw: dict) -> dict:
    container = _g(raw["records"], "locations")
    if isinstance(container, list):
        container = container[0]
    if not isinstance(container, dict):
        raise RuntimeError("❗ API locations 欄位非 dict，請確認授權狀態")

    cities = _g(container, "location", [])
    if not cities:
        raise RuntimeError("❗ API 有 locations 但無 city 資料")

    res = {}
    for city in cities:
        name   = (_g(city, "locationName") or _g(city, "LocationName")).strip()
        welems = _g(city, "weatherElement", [])
        e_map  = { _g(e, "elementName"): e for e in welems if _g(e, "elementName") in ELEMS }

        times  = _g(e_map["Wx"], "time", [])
        blocks = []
        for i, t in enumerate(times):
            blk = {"start": _g(t, "startTime")[:16], "end": _g(t, "endTime")[:16]}
            for en, field in ELEMS.items():
                ev = _g(_g(e_map[en], "time", [])[i], "elementValue", [{}])[0]
                blk[field] = _g(ev, "value")
            blocks.append(blk)
        res[name] = blocks
    return res

# ===== 4. 主程式 =====
def main():
    raw  = _fetch()
    data = _parse(raw)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "timestamp": int(time.time()),
        "source"   : "中央氣象署‧F-D0047-089",
        "source_url": BASE_URL,
        "cities"   : data
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ forecast_weather.json 已更新")

if __name__ == "__main__":
    main()
