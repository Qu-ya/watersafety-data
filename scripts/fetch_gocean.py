#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
擷取 GoOcean 即時海象資料，存成 quiz/gocean_live.json
※ 網頁結構若變動，需要自行調整 selector
"""
import json, re, time, requests
from bs4 import BeautifulSoup
from pathlib import Path

OUT  = Path(__file__).resolve().parent.parent / "quiz" / "gocean_live.json"
URL  = "https://goocean.namr.gov.tw/Information"

def scrape() -> dict:
    r   = requests.get(URL, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # ⬇️ 以下 selector 依 GoOcean 畫面調整
    site  = soup.select_one("#SeaCode").get_text(strip=True)
    wave  = soup.select_one(".waveHeight span").text          # 浪高
    wind  = soup.select_one(".windSpeed span").text           # 風速
    water = soup.select_one(".waterTemp span").text           # 水溫
    risk  = soup.select_one(".riskLevel").text                # 風險等級文字

    return {
        "timestamp"   : int(time.time()),
        "site"        : site,
        "wave_height" : wave,
        "wind_speed"  : wind,
        "water_temp"  : water,
        "risk_level"  : risk,
        "source"      : URL
    }

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = scrape()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已更新 {OUT}：{data}")
