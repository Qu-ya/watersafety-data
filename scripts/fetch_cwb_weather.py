#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓中央氣象署 F-D0047-089（未來 7 日市區預報）
輸出 quiz/forecast_weather.json
"""

import os
import json
import time
import requests
from pathlib import Path

# ══════════ 1. 設定 API KEY、URL 與輸出路徑 ══════════
API_KEY = os.environ["CWB_API_KEY"]
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"
PARAMS = {
    "Authorization": API_KEY,
    "format":        "JSON",
    # 若要篩選城市，可加：
    # "locationName": "臺北市,新北市,高雄市"
}
OUT_PATH = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

# ══════════ 2. 工具函式：從 ElementValue 拿值 ══════════
def _first_time_block(elem: dict) -> dict:
    """回傳 elem 裡的第一個時段物件（大寫 Time 或 小寫 time）"""
    times = elem.get("Time") or elem.get("time") or []
    return times[0] if times else {}

def _get_elem_value(elem: dict) -> str:
    """
    從一個 weatherElement 的第一個時段，取 ElementValue 中的第一個值
    （支援大寫 ElementValue 或 小寫 elementValue）
    """
    block = _first_time_block(elem)
    vals  = block.get("ElementValue") or block.get("elementValue") or []
    if isinstance(vals, list) and vals:
        first = vals[0]
        for v in first.values():
            return v
    return ""  # 若無任何值，回傳空字串

# ══════════ 3. 主程式流程 ══════════
def main():
    # --- 3.1 取得 API 原始資料 ---
    resp = requests.get(BASE_URL, params=PARAMS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("success") != "true":
        raise RuntimeError(f"CWB API 回傳失敗：{data}")

    # --- 3.2 抽出 locations 清單（支援大/小寫） ---
    recs     = data["records"]
    locs     = recs.get("locations") or recs.get("Locations") or []
    if not locs:
        raise RuntimeError(f"找不到 locations，keys={list(recs.keys())}")
    loc_list = locs[0].get("location") or locs[0].get("Location") or []

    # --- 3.3 逐一處理每個城市的三個元素 ---
    forecast_data = {}
    for loc in loc_list:
        city_name = loc.get("locationName") or loc.get("LocationName", "").strip()
        elems     = loc.get("weatherElement") or loc.get("WeatherElement") or []

        temp_elem = next(e for e in elems if (e.get("elementName") or e.get("ElementName")) == "溫度")
        rain_elem = next(e for e in elems if (e.get("elementName") or e.get("ElementName")) == "3小時降雨機率")
        wx_elem   = next(e for e in elems if (e.get("elementName") or e.get("ElementName")) == "天氣現象")

        forecast_weather = _get_elem_value(wx_elem)    # e.g. "多雲時晴"
        rain_pct         = _get_elem_value(rain_elem)  # e.g. "30"
        temp_val         = _get_elem_value(temp_elem)  # e.g. "26"

        forecast_data[city_name] = {
            "forecast_weather": forecast_weather,
            "rain_pct"        : rain_pct,
            "min_temp"        : temp_val,
            "max_temp"        : temp_val,
        }

    # --- 3.4 組出最終 JSON，並寫入檔案 ---
    output = {
        "timestamp" : int(time.time()),
        "source_url": resp.url,
        "cities"    : forecast_data
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 寫入 {OUT_PATH}")

if __name__ == "__main__":
    main()
