#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取中央氣象署 F-C0032-001 今明 36 小時預報
* 一次抓 22 個縣市
* 萃取：天氣現象(Wx)、12h降雨機率(PoP)、最低溫(MinT)、最高溫(MaxT)
* 存成 quiz/weather_live.json（dict 以城市為 key，GPT 讀檔後再依需要篩選）
"""

import json, os, time, requests
from pathlib import Path

# 22 個縣市（順序可自訂，名稱須與氣象局資料一致）
CITIES = [
    "基隆市","臺北市","新北市","桃園市","新竹市","新竹縣",
    "苗栗縣","臺中市","彰化縣","南投縣","雲林縣","嘉義市",
    "嘉義縣","臺南市","高雄市","屏東縣","宜蘭縣","花蓮縣",
    "臺東縣","澎湖縣","金門縣","連江縣"
]

API_KEY = os.environ["CWB_API_KEY"]
URL = (
    "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    f"?locationName={','.join(CITIES)}"
    "&format=JSON"
    f"&Authorization={API_KEY}"
)

OUT = Path(__file__).resolve().parent.parent / "quiz" / "weather_live.json"

def _pick(elem_list, code: str) -> str:
    """從 weatherElement 中找出指定 elementName 的第一筆參數值"""
    return next(e for e in elem_list if e["elementName"] == code)["time"][0]["parameter"]["parameterName"]

def main() -> None:
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    data = r.json()

    weather_dict = {}
    for loc in data["records"]["location"]:
        name = loc["locationName"]
        el   = loc["weatherElement"]
        weather_dict[name] = {
            "weather"     : _pick(el, "Wx"),
            "pop_12h_pct" : _pick(el, "PoP"),
            "temp_min_C"  : _pick(el, "MinT"),
            "temp_max_C"  : _pick(el, "MaxT"),
        }

    out_json = {
        "timestamp" : int(time.time()),
        "source_url": URL,
        "cities"    : weather_dict
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已寫入 {OUT}")

if __name__ == "__main__":
    main()
