# quick_gocean_test.py
import requests, pprint

url = "https://goocean.namr.gov.tw/Main/GetPageData"

payload = {
    "time":      "2025051902",
    "type":      "waveHeight,wind,waterTemp,riskLevel,sports-classification",
    "action":    "12",
    "ValueMode": "t3",
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

r = requests.post(url, data=payload, headers=headers, timeout=10)
r.raise_for_status()           # 若非 200 會丟例外
data = r.json()                # 把 JSON 轉成 Python dict
pprint.pprint(data)            # 漂亮列印
