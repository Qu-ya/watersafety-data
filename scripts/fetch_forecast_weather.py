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

# ═══════════ 1. 設定 API 與路徑 ═══════════
API_KEY = os.environ["CWB_API_KEY"]
BASE    = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"
PARAMS  = {
    "Authorization": API_KEY,
    "format":        "JSON",
    # 若要鎖定特定城市，可加：
    # "locationName": "臺北市,新北市,高雄市"
}
OUT = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"


# ═══════════ 2. 工具函式：取第一筆時段、並抽值 ═══════════
def _first_time(elem: dict) -> dict:
    """回傳 elem["Time"][0] 或 elem["time"][0]（若有）"""
    times = elem.get("Time") or elem.get("time") or []
    return times[0] if times else {}

def get_param_value(elem: dict) -> str:
    """
    取『parameterValue』，對應 天氣現象 / 降雨機率
    """
    first = _first_time(elem)
    # 小寫 parameter 或 大寫 Parameter
    plist = first.get("parameter") or first.get("Parameter") or []
    if plist and isinstance(plist, list):
        return plist[0].get("parameterValue", "")
    return ""

def get_element_value(elem: dict) -> str:
    """
    取『ElementValue』裡的第一個數值（例如 Temperature）
    """
    first = _first_time(elem)
    ev_list = first.get("ElementValue") or first.get("elementValue") or []
    if ev_list and isinstance(ev_list, list):
        ev = ev_list[0]
        # 取第一個 key 的值
        for v in ev.values():
            return v
    return ""


# ═══════════ 3. 主流程 ═══════════
def main():
    # 3.1 請求 CWB API
    resp = requests.get(BASE, params=PARAMS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("success") != "true":
        raise RuntimeError(f"CWB API 回傳失敗: {data}")

    # 3.2 取 records 裡的 locations / Locations
    recs = data["records"]
    locs = recs.get("locations") or recs.get("Locations") or []
    if not locs:
        raise RuntimeError(f"找不到 locations，keys={list(recs.keys())}")
    loc_list = locs[0].get("location") or locs[0].get("Location") or []

    # 3.3 逐一處理各縣市
    weather_dict = {}
    for loc in loc_list:
        name = loc.get("locationName") or loc.get("LocationName", "")
        elems = loc.get("weatherElement") or loc.get("WeatherElement") or []

        # 3.3.1 找出三個關鍵元素
        temp_elem = next(
            e for e in elems
            if (e.get("elementName") or e.get("ElementName")) == "溫度"
        )
        rain_elem = next(
            e for e in elems
            if (e.get("elementName") or e.get("ElementName")) == "3小時降雨機率"
        )
        wx_elem   = next(
            e for e in elems
            if (e.get("elementName") or e.get("ElementName")) == "天氣現象"
        )

        # 3.3.2 取值
        fw = get_param_value(wx_elem)      # 天氣現象 → parameterValue
        rp = get_param_value(rain_elem)    # 3小時降雨機率 → parameterValue
        tv = get_element_value(temp_elem)  # 溫度 → ElementValue

        weather_dict[name] = {
            "forecast_weather": fw,
            "rain_pct"        : rp,
            "min_temp"        : tv,
            "max_temp"        : tv,
        }

    # 3.4 輸出 JSON
    out = {
        "timestamp" : int(time.time()),
        "source_url": resp.url,
        "cities"    : weather_dict
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 寫入 {OUT}")


if __name__ == "__main__":
    main()
