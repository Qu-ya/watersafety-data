#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動下載體育署救生員題庫 PDF → 解析 → 輸出 JSON
"""

import io
import datetime
import pathlib
import re
import requests
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup

# 1. 輸出資料夾
OUTDIR = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)

# 2. Session & headers
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://isports.sa.gov.tw/apps/Essay.aspx",
}

# 3. 題庫列表頁 URL
LIST_URL = (
    "https://isports.sa.gov.tw/apps/Essay.aspx"
    "?SYS=LGM"
    "&MENU_CD=M10"
    "&ITEM_PRG_CD=3"        # 補上這行
    "&ITEM_CD=T07"
    "&MENU_PRG_CD=3"        # 確保兩個 PRG 參數都在
)



print("GET list page …", LIST_URL)
resp1 = session.get(LIST_URL, headers=HEADERS, timeout=30)
resp1.raise_for_status()
html = resp1.text

# 4. 解析 ASP.NET form 隱藏欄位
soup = BeautifulSoup(html, "lxml")
form = soup.find("form", id="aspnetForm")
if not form:
    print("HTML 前 300 字：\n", html[:300])
    raise RuntimeError("找不到 ASP.NET Form")

data = {}
for inp in form.find_all("input", {"type": "hidden"}):
    name = inp.get("name")
    if name:
        data[name] = inp.get("value", "")

# 5. 觸發下載的欄位
data["__EVENTTARGET"]   = "ctl00$IsportContent$FileDownLoad"
data["__EVENTARGUMENT"] = ""

# 6. POST 下載 PDF
DOWNLOAD_URL = f"https://isports.sa.gov.tw{form['action']}"
print("POST download form …", DOWNLOAD_URL)
resp2 = session.post(DOWNLOAD_URL, headers=HEADERS, data=data, timeout=60)
ct = resp2.headers.get("content-type", "")
if resp2.status_code != 200 or not ct.startswith("application/pdf"):
    print("Response headers:", resp2.headers)
    print("Response text (first 300 chars):\n", resp2.text[:300])
    raise RuntimeError(f"下載失敗：HTTP {resp2.status_code} - {ct}")

pdf_bytes = resp2.content
print("PDF OK ✔", len(pdf_bytes), "bytes")

# 7. 存成 quiz_114.pdf（今年是114）
year_tag = datetime.date.today().year - 1911
pdf_path = OUTDIR / f"quiz_{year_tag}.pdf"
pdf_path.write_bytes(pdf_bytes)
print("Saved PDF →", pdf_path.name)

# 8. 解析 PDF → 組 rows
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text() or ""
        for n, q, ans in re.findall(r"(\d+)\.([^\n]+?)\(([ABCDOX])\)", txt):
            typ = "TF" if ans in "OX" else "MC"
            rows.append({
                "id":       f"Q{int(n):04}",
                "chapter":  f"CH{int(n)//100+1:02}",
                "type":     typ,
                "q":        q.strip(),
                "choices":  "" if typ=="TF" else "A|B|C|D",
                "ans":      ans,
                "explain":  ""
            })

# 9. 輸出 JSON
json_path = OUTDIR / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(
    json_path,
    orient="records",
    indent=2,
    force_ascii=False
)
print("Saved JSON →", json_path.name, f"({len(rows)} questions)")
