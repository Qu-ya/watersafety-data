# scripts/fetch_forecast_weather.py
import os, json, time
import requests
from pathlib import Path

API_KEY = os.environ["CWB_API_KEY"]
CITIES = ["臺北市", "新北市", "台南市", "高雄市"]  # 你可依需求擴增

URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089?Authorization={API_KEY}&format=JSON&locationName=" + ",".join(CITIES)

OUT = Path(__file__).resolve().parent.parent / "quiz" / "forecast_weather.json"

def _pick_first_param(elem, code):
    return next(e for e in elem if e["elementName"] == code)["time"][0]["parameter"]["parameterName"]

def main():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    data = r.json()

    weather_dict = {}
    for loc in data["records"]["locations"][0]["location"]:
        name = loc["locationName"]
        el = loc["weatherElement"]
        weather_dict[name] = {
            "forecast_weather": _pick_first_param(el, "Wx"),
            "rain_pct": _pick_first_param(el, "PoP"),
            "min_temp": _pick_first_param(el, "MinT"),
            "max_temp": _pick_first_param(el, "MaxT"),
        }

    out_json = {
        "timestamp": int(time.time()),
        "source_url": URL,
        "cities": weather_dict
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 寫入 {OUT}")

if __name__ == "__main__":
    main()
