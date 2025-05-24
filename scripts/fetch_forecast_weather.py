#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓中央氣象署 F-D0047-089（未來 7 日市區預報）"""

import os, json, time, requests
from pathlib import Path

API_KEY = os.environ["CWB_API_KEY"]
BASE = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"

PARAMS = {
    "Authorization": API_KEY,
    "format": "JSON",
    # 若要指定城市可加 "locationName": "臺北市,新北市,高雄市"
}

OUT = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

def _pick(elem_list, code):
    """
    支援 CWB 兩套回傳格式：
    - 小寫 elementName/time/parameter/parameterName
    - 大寫 ElementName/Time/ElementValue
    回傳對應 code 的「第一筆」資料值
    """
    for e in elem_list:
        # 取得 element 名稱：支援小寫或大寫
        name = e.get("elementName") or e.get("ElementName")
        if name != code:
            continue

        # 取得時間列表：支援小寫或大寫
        times = e.get("time") or e.get("Time") or []
        if not times:
            continue

        first = times[0]

        # 小寫 parameter
        if "parameter" in first:
            return first["parameter"]["parameterName"]

        # 小寫 elementValue (極少見)
        if "elementValue" in first:
            ev = first["elementValue"][0]
            # 回傳第一個 key 的值
            return ev[next(iter(ev.keys()))]

        # 大寫 ElementValue
        if "ElementValue" in first:
            ev = first["ElementValue"][0]
            return ev[next(iter(ev.keys()))]

    # 如果跑完都沒找到就報錯
    raise RuntimeError(f"找不到 code={code} 對應的 element")

def main():
    r = requests.get(BASE, params=PARAMS, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("success") != "true":
        raise RuntimeError(f"CWB API 回傳失敗: {data}")

    weather_dict = {}
    recs = data["records"]

    # 同時支援 小寫 locations & 大寫 Locations
    if "locations" in recs and isinstance(recs["locations"], list):
        loc_list = recs["locations"][0]["location"]
    elif "Locations" in recs and isinstance(recs["Locations"], list):
        loc_list = recs["Locations"][0]["Location"]
    else:
        raise RuntimeError(f"找不到任何 Location 清單，keys={list(recs.keys())}")

    for loc in loc_list:
        # 先抓第一個地點的 elementName 列表，用來觀察有哪些欄位
        el_list = loc.get("weatherElement") or loc.get("WeatherElement")
        import sys
        # 列印所有 elementName（同時支援大寫/小寫）
        names = [e.get("elementName") or e.get("ElementName") for e in el_list]
        print("DEBUG elementName list:", names, file=sys.stderr)
        # 印出第一筆時間資料（用來確認子欄位 keys）
        first = el_list[0].get("time") or el_list[0].get("Time")
        print("DEBUG first time entry keys:", list(first[0].keys()), file=sys.stderr)
        sys.exit(0)

        weather_dict[name] = {
            "forecast_weather": _pick(el_list, "Wx"),
            "rain_pct"       : _pick(el_list, "PoP"),
            "min_temp"       : _pick(el_list, "MinT"),
            "max_temp"       : _pick(el_list, "MaxT"),
        }

    out_json = {
        "timestamp": int(time.time()),
        "source_url": r.url,
        "cities": weather_dict
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 寫入 {OUT}")

if __name__ == "__main__":
    main()
