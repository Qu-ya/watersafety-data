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
    """取 weatherElement 第一筆參數值"""
    return next(e for e in elem_list if e["elementName"] == code)["time"][0]["parameter"]["parameterName"]

def main():
    r = requests.get(BASE, params=PARAMS, timeout=10)
    r.raise_for_status()
    data = r.json()

    if data.get("success") != "true":
        raise RuntimeError(f"CWB API 回傳失敗: {data}")

    weather_dict = {}
    recs = data["records"]
    if "locations" in recs:
        loc_list = recs["location"]

    for loc in loc_list:

        name = loc["locationName"]
        el = loc["weatherElement"]
        weather_dict[name] = {
            "forecast_weather": _pick(el, "Wx"),
            "rain_pct":        _pick(el, "PoP"),
            "min_temp":        _pick(el, "MinT"),
            "max_temp":        _pick(el, "MaxT"),
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
