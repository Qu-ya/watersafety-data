#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中央氣象署 F-D0047-089（22 縣市未來 1 週預報）
→ 產生 quiz/forecast_weather.json
欄位：Wx(天氣)‧PoP12h(降雨%)‧MinT‧MaxT‧WS(風速 m/s)
"""

import os, json, time, requests
from pathlib import Path

# ===== 1. 基本設定 =====
API_KEY  = os.environ["CWB_API_KEY"]                    # GitHub Secrets
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"
PARAMS   = { "Authorization": API_KEY, "format": "JSON" }
OUT_PATH = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

ELEMS = {
    "Wx"     : "weather",
    "PoP12h" : "rain_pct",
    "MinT"   : "min_temp",
    "MaxT"   : "max_temp",
    "WS"     : "wind_speed",
}

def _g(obj: dict, key: str, default=""):
    """大小寫皆可取值"""
    return obj.get(key) or obj.get(key.lower()) or default

# ===== 2. 下載並判斷授權狀態 =====
def _fetch() -> dict:
    r = requests.get(BASE_URL, params=PARAMS, timeout=20)
    r.raise_for_status()
    data = r.json()

    # ① success ≠ "true"
    if data.get("success") != "true":
        msg = data.get("result", {}).get("message", data)
        raise RuntimeError(f"❗ CWA API 回傳失敗：{msg}")

    # ② records 為空字串 ➜ 尚未啟用資料集 或 當日流量超限
    if isinstance(data.get("records"), str):
        msg = data.get("result", {}).get("message", "records 為空字串")
        raise RuntimeError(
            "❗ CWA records 空白：{}\n👉 請確認『資料開放→我的授權資料集』已將 F-D0047-089 狀態設為「已啟用」，"
            "且當日流量未超過配額 (30,000)".format(msg)
        )
    return data

# ===== 3. 解析 22 縣市 =====
def _parse(raw: dict) -> dict:
    container = _g(raw["records"], "locations")
    if isinstance(container, list):
        container = container[0]
    if not isinstance(container, dict):
        raise RuntimeError("❗ API locations 欄位不是 dict，請檢查授權")

    cities = _g(container, "location", [])
    if not cities:
        raise RuntimeError("❗ API 無 city 資料，請檢查授權")

    result = {}
    for city in cities:
        name   = (_g(city, "locationName") or _g(city, "LocationName")).strip()
        welems = _g(city, "weatherElement", [])
        e_map  = { _g(e, "elementName"): e for e in welems if _g(e, "elementName") in ELEMS }

        times  = _g(e_map["Wx"], "time", [])
        blocks = []
        for i, t in enumerate(times):
            blk = { "start": _g(t, "startTime")[:16], "end": _g(t, "endTime")[:16] }
            for en, field in ELEMS.items():
                time_arr = _g(e_map[en], "time", [])
                ev_arr   = _g(time_arr[i] if i < len(time_arr) else {}, "elementValue", [])
                blk[field] = _g(ev_arr[0] if ev_arr else {}, "value")
            blocks.append(blk)
        result[name] = blocks
    return result

# ===== 4. 主流程 =====
def main():
    raw  = _fetch()
    data = _parse(raw)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "timestamp": int(time.time()),
        "source"   : "中央氣象署（F-D0047-089）",
        "source_url": BASE_URL,
        "cities"   : data
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ forecast_weather.json 已寫入")

if __name__ == "__main__":
    main()
