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

# 1. 初始化 session & 共同 headers
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://isports.sa.gov.tw/",
}

# 2. 取得題庫列表頁 (Essay.aspx)
LIST_URL = (
  "https://isports.sa.gov.tw/apps/Essay.aspx"
  "?SYS=LGM"
  "&MENU_CD=M10"
  "&ITEM_PRG_CD=3"
  "&ITEM_CD=T07"
)
resp1 = session.get(LIST_URL, headers=HEADERS, timeout=30)
resp1.raise_for_status()

# 3. 用 BeautifulSoup 抓出 <form>、所有 hidden inputs
soup = BeautifulSoup(resp1.text, "lxml")
form = soup.find("form", id="aspnetForm")
if not form:
    raise RuntimeError("找不到 ASP.NET Form")

action = form["action"]
POST_URL = f"https://isports.sa.gov.tw{action}"

# 收集所有隱藏欄位
data = {
    tag["name"]: tag.get("value", "")
    for tag in form.find_all("input", {"type": "hidden"})
    if tag.has_attr("name")
}

# 4. 設定觸發下載的欄位
data["__EVENTTARGET"]   = "ctl00$IsportContent$FileDownLoad"
data["__EVENTARGUMENT"] = ""

# 5. POST 去 FDownload.aspx 下載 PDF
resp2 = session.post(POST_URL, data=data, headers=HEADERS, timeout=30)
ct = resp2.headers.get("content-type", "")
if resp2.status_code != 200 or "application/pdf" not in ct:
    raise RuntimeError(f"下載失敗：HTTP {resp2.status_code} - {ct}")

pdf_bytes = resp2.content
print("✅ PDF OK", len(pdf_bytes), "bytes")

# 6. 存 PDF
year_tag = datetime.date.today().year - 1911  # 2025→114
outdir = pathlib.Path(__file__).parent.parent / "quiz"
outdir.mkdir(exist_ok=True)
pdf_path = outdir / f"quiz_{year_tag}.pdf"
pdf_path.write_bytes(pdf_bytes)
print("Saved PDF →", pdf_path.name)

# 7. 解析 PDF → rows
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text() or ""
        for n, q, ans in (
            pd.np.fromiter  # workaround if pd.np missing; otherwise just re.findall
            for _ in ()
        ):
            pass  # 忽略
        # 直接用 regex 提取
        import re
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

# 8. 輸出 JSON
json_path = outdir / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(
    json_path, orient="records", indent=2, force_ascii=False
)
print(f"Saved JSON → {json_path.name} ({len(rows)} questions)")
