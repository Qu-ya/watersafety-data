#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動下載體育署救生員題庫 PDF，解析後輸出 JSON。
"""

import io, re, datetime, pathlib, requests
import pdfplumber, pandas as pd

# 1. 原列表頁網址
LIST_URL = (
    "https://isports.sa.gov.tw/apps/Essay.aspx"
    "?SYS=LGM&MENU_PRG_CD=3&ITEM_PRG_CD=3&ITEM_CD=T07"
)
# 請求 Header 偽裝瀏覽器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://isports.sa.gov.tw/apps/Essay.aspx",
}

# 2. GET 列表頁，直接用 regex 抓出 PDF 路徑
resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
html = resp.text
m = re.search(r"downLoadFileWithName\('([^']+\.pdf)'", html)
if not m:
    raise RuntimeError("在列表頁找不到 PDF 路徑，請檢查 HTML")
rel_path = m.group(1)  # e.g. LGM/09/04/.../xxx.pdf
PDF_URL = f"https://isports.sa.gov.tw/{rel_path}"
print("PDF URL →", PDF_URL)

# 3. Download PDF
resp2 = requests.get(PDF_URL, headers=HEADERS, timeout=30)
ct = resp2.headers.get("content-type", "")
if resp2.status_code != 200 or not ct.startswith("application/pdf"):
    raise RuntimeError(f"下載失敗：HTTP {resp2.status_code} - {ct}")
pdf_bytes = resp2.content
print("✅ PDF OK", len(pdf_bytes), "bytes")

# 4. 存成 quiz_YYYY.pdf
year_tag = datetime.date.today().year - 1911  # 2025→114
outdir = pathlib.Path(__file__).parent.parent / "quiz"
outdir.mkdir(exist_ok=True)
pdf_path = outdir / f"quiz_{year_tag}.pdf"
pdf_path.write_bytes(pdf_bytes)
print("Saved PDF →", pdf_path.name)

# 5. 解析 PDF → rows
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text() or ""
        for n, q, ans in re.findall(r"(\d+)\.([^\n]+?)\(([ABCDOX])\)", txt):
            typ = "TF" if ans in "OX" else "MC"
            rows.append({
                "id":   f"Q{int(n):04}",
                "chapter": f"CH{int(n)//100+1:02}",
                "type": typ,
                "q":    q.strip(),
                "choices": "" if typ=="TF" else "A|B|C|D",
                "ans":  ans,
                "explain": ""
            })

# 6. 輸出 JSON
json_path = outdir / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(json_path, orient="records",
                          indent=2, force_ascii=False)
print("Saved JSON →", json_path.name, f"({len(rows)} questions)")
