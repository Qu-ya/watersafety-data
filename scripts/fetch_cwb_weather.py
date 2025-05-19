#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取中央氣象署 3 小時逐時預報（F-C0032-001）
* 只取「臺北市」示範
* 萃取：氣溫（T）、10 分鐘平均風速（WS）、6 小時降雨機率（PoP6h）
* 存成 quiz/weather_live.json
"""

import json, os, time, requests
from pathlib import Path

API_KEY = os.environ["CWB_API_KEY"]              # ← 來自 Secrets
URL = (
    "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    "?locationName=臺北市"
    "&format=JSON"
    f"&Authorization={API_KEY}"
)

OUT = Path(__file__).resolve().parent.parent / "quiz" / "weather_live.json"

def main() -> None:
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    data = r.json()
    # --- DEBUG 先看看有哪些欄位 ---
    #for e in data["records"]["location"][0]["weatherElement"]:
    #    print("→", e["elementName"])
    #quit()        # 列完就先結束程式
    # ---------------------------------


    el = data["records"]["location"][0]["weatherElement"]

    # 取三個欄位（T, WS, PoP6h）
    get_val = lambda elem_code: next(
        e for e in el if e["elementName"] == elem_code
    )["time"][0]["parameter"]["parameterName"]    # ← parameter 裡面的 parameterName
    
    out = {
        "timestamp"   : int(time.time()),
        "location"    : "臺北市",
        "weather"     : get_val("Wx"),      # 天氣現象文字
        "pop_12h_pct" : get_val("PoP"),     # 12 小時降雨機率 %
        "temp_min_C"  : get_val("MinT"),    # 最低溫
        "temp_max_C"  : get_val("MaxT"),    # 最高溫
        "source_url"  : URL,
    }


    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已寫入 {OUT}\n", json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
