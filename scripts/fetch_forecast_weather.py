#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓中央氣象署 F-D0047-089（未來 7 日市區預報）
自動產生 quiz/forecast_weather.json
"""

import os
import json
import time
import requests
from pathlib import Path

# ═══════════ 1. 設定 API、路徑 ═══════════
API_KEY = os.environ["CWB_API_KEY"]
BASE    = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"
PARAMS  = {
    "Authorization": API_KEY,
    "format":        "JSON",
    # "locationName": "臺北市,新北市,高雄市"  # 如要指定城市，可解開此行
}
OUT = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

# ═══════════ 2. 工具函式：取 ElementValue 或 parameter ═══════════
def _get_val(elem: dict, key: str) -> str:
    """
    從 weatherElement 的 elem 中，取得第一筆時段的 key 值。
    支援大小寫：
      - 大寫版：Time、ElementValue
      - 小寫版：time、parameter
    """
    # 先取時間陣列（Pref: 大寫 'Time'，否則 'time'）
    times = elem.get("Time") or elem.get("time") or []
    if not times:
        raise RuntimeError(f"No time data for element: {elem}")

    first = times[0]

    # 優先用大寫 ElementValue
    if "ElementValue" in first:
        ev_list = first["ElementValue"]
    # 否則用小寫 parameter
    elif "parameter" in first:
        ev_list = first["parameter"]
    else:
        raise RuntimeError(f"No ElementValue/parameter in: {first}")

    if not isinstance(ev_list, list) or not ev_list:
        raise RuntimeError(f"Empty ElementValue/parameter list: {first}")

    return ev_list[0].get(key, "")

# ═══════════ 3. 主流程 ═══════════
def main():
    # 3.1 呼叫 API
    r = requests.get(BASE, params=PARAMS, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("success") != "true":
        raise RuntimeError(f"CWB API 回傳失敗: {data}")

    # 3.2 取出 records
    recs = data["records"]

    # 3.3 支援大小寫 locations / Locations
    if "locations" in recs and isinstance(recs["locations"], list):
        loc_list = recs["locations"][0]["location"]
    elif "Locations" in recs and isinstance(recs["Locations"], list):
        loc_list = recs["Locations"][0]["Location"]
    else:
        raise RuntimeError(f"找不到任何 Location 清單，keys={list(recs.keys())}")

    # 3.4 逐一處理每個城市
    weather_dict = {}
    for loc in loc_list:
        name    = loc.get("locationName") or loc.get("LocationName")
        el_list = loc.get("weatherElement") or loc.get("WeatherElement")

        # 3.4.1 找出需要的三個元素
        temp_elem = next(
            e for e in el_list
            if (e.get("elementName") or e.get("ElementName")) == "溫度"
        )
        rain_elem = next(
            e for e in el_list
            if (e.get("elementName") or e.get("ElementName")) == "3小時降雨機率"
        )
        wx_elem   = next(
            e for e in el_list
            if (e.get("elementName") or e.get("ElementName")) == "天氣現象"
        )

        # 3.4.2 用 _get_val() 取值
        forecast_weather = _get_val(wx_elem,   "Wx")
        rain_pct         = _get_val(rain_elem, "PoP")
        temp_val         = _get_val(temp_elem, "Temperature")
        min_temp         = _get_val(temp_elem, "MinT") or temp_val
        max_temp         = _get_val(temp_elem, "MaxT") or temp_val

        weather_dict[name] = {
            "forecast_weather": forecast_weather,
            "rain_pct"         : rain_pct,
            "min_temp"         : min_temp,
            "max_temp"         : max_temp,
        }

    # 3.5 輸出 JSON
    out_json = {
        "timestamp" : int(time.time()),
        "source_url": r.url,
        "cities"    : weather_dict
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 寫入 {OUT}")

# 執行點
if __name__ == "__main__":
    main()
