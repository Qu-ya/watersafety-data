#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動下載體育署救生員題庫 PDF → 解析 → 輸出 JSON
"""

import io
import datetime
import pathlib
import requests
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup

# 0. 準備輸出資料夾
OUTDIR = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)

# 1. 建立 session & headers
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://isports.sa.gov.tw/apps/Essay.aspx",
}

# 2. 取得題庫列表頁 (Essay.aspx)
LIST_URL = (
    "https://isports.sa.gov.tw/apps/Essay.aspx"
    "?SYS=LGM"
    "&MENU_CD=M10"
    "&ITEM_PRG_CD=3"
    "&ITEM_CD=T07"
)
print("GET list page …", LIST_URL)
resp = session.get(LIST_URL, headers=HEADERS, timeout=30)
resp.raise_for_status()
html = resp.text

# 3. 用 BeautifulSoup 找到那個 <form id="aspnetForm">
soup = BeautifulSoup(html, "lxml")
form = soup.find("form", id="aspnetForm")
if not form:
    raise RuntimeError("找不到 ASP.NET Form")

# 4. 把 form 裡所有 hidden input 都收進一個 dict
data = {}
for inp in form.find_all("input", type="hidden"):
    name = inp.get("name")
    val  = inp.get("value", "")
    if name:
        data[name] = val

# 5. 再按那個「下載」按鈕的 PostBack target
data["__EVENTTARGET"]  = "ctl00$IsportContent$FileDownLoad"
data["__EVENTARGUMENT"] = ""   # 空字串

# 6. POST 到 FDownload.aspx 拿到 PDF bytes
DOWNLOAD_URL = "https://isports.sa.gov.tw/apps/FDownload.aspx"
print("POST download form …", DOWNLOAD_URL)
resp2 = session.post(DOWNLOAD_URL, headers=HEADERS, data=data, timeout=30)
ct = resp2.headers.get("Content-Type", "")
if not ct.startswith("application/pdf"):
    raise RuntimeError(f"下載失敗：HTTP {resp2.status_code} – {ct}")
pdf_bytes = resp2.content
print("PDF OK ✔", len(pdf_bytes), "bytes")

# 7. 存檔
year_tag = datetime.date.today().year - 1911   # 2025→114
pdf_path = OUTDIR / f"quiz_{year_tag}.pdf"
pdf_path.write_bytes(pdf_bytes)

# 8. 用 pdfplumber 解析 → 組成 rows
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text() or ""
        for n, q, ans in pd.np.findall(r"(\d+)\.([^\n]+)\(([ABCDOX])\)", txt):
            typ = "TF" if ans == "O" else "MC"
            rows.append({
                "id":      f"Q{int(n):04}",
                "chapter": f"CH{int(n)//100+1:02}",
                "type":    typ,
                "q":       q.strip(),
                "choices": "" if typ=="TF" else "A|B|C|D",
                "ans":     ans,
                "explain": "",
            })

# 9. 輸出 JSON
json_path = OUTDIR / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(
    json_path,
    orient="records",
    indent=2,
    force_ascii=False
)
print("Saved", json_path, "with", len(rows), "questions")
