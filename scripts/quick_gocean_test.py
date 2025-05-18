# quick_gocean_test.py
import requests, pprint

url = "https://goocean.namr.gov.tw/Main/GetPageData"
payload = {
    "time": "2025051902",                          # ← 把這四行改成你剛剛在 DevTools 看到的值
    "type": "sports-classification,SwellsAlert",
    "action": "12",
    "ValueMode": "t3",
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

r = requests.post(url, data=payload, headers=headers, timeout=10)
r.raise_for_status()            # 如果回傳不是 200 會直接丟例外
data = r.json()                 # 把 JSON 轉成 Python dict
pprint.pp(data)                 # 漂亮地印出來
